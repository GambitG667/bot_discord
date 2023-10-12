import logging
import aiosqlite
import asyncio
from dataclasses import dataclass
import os
import signal

aiosqlite.register_adapter(bool, int)
aiosqlite.register_converter("BOOLEAN", lambda v: v != '0')

logger = logging.getLogger(__name__)
# logging.getLogger("aiosqlite").setLevel(logging.INFO)

class Database:
    @dataclass
    class Voting:
        message_id: int
        title: str
        description: str
        author_id: int
        is_open: bool

    @dataclass
    class Vote:
        user_id: int
        voting_id: int
        type: bool

    def __init__(self, path):
        self.path = path
        logger.debug("Иницилизация объекта базы данных")

    @classmethod
    async def open(cls, path):
        obj = cls(path)
        await obj.create_tables()
        return obj

    async def create_tables(self):
        if not os.path.isfile(self.path):
            logger.warning(f"Базы данных {self.path} не существует. В этом случае она будет создана")

        async with aiosqlite.connect(self.path) as db: 
            
            await db.executescript("""
            CREATE TABLE IF NOT EXISTS votings (
                "message_id" INTEGER PRIMARY KEY,
                "title" TEXT NOT NULL,
                "description" TEXT NOT NULL,
                "author_id" INTEGER NOT NULL,
                "is_open" BOOLEAN NOT NULL DEFAULT 1,
                "anonym" BOOLEAN NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS votes (
                "user_id" INTEGER NOT NULL,
                "voting_id" INTEGER NOT NULL REFERENCES votings (message_id),
                "type" BOOLEAN NOT NULL,
                PRIMARY KEY(user_id, voting_id)
            );
            """)
            
            logger.info("Создание таблиц базы данных если их нет")
            await db.commit()

    async def get(self, query, params):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(query, params)
            return (await cursor.fetchall())

    async def get_one(self, query, params):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(query, params)
            return (await cursor.fetchone())

    async def put(self, query, params):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(query, params)
            await db.commit()

    async def start_voting(self, message_id, title, desc, author_id):
        query = "INSERT INTO votings VALUES (?, ?, ?, ?, 1, 0)"
        await self.put(query, (message_id, title, desc, author_id))

    async def close_voting(self, message_id):
        query = "UPDATE votings SET is_open = 0 WHERE message_id = ?"
        await self.put(query, (message_id,))

    async def vote(self, user_id, voting_id, typ):
        query = "REPLACE INTO votes VALUES (?, ?, ?)"
        await self.put(query, (user_id, voting_id, typ))

    async def get_vote(self, user_id, voting_id):
        query = "SELECT * FROM votes WHERE user_id = ? AND voting_id = ?"
        t = await self.get_one(query, (user_id, voting_id))
        if t is not None:
            return self.Vote(*t)

    def __del__(self):
        logger.info("Уничтожение объекта базы данных")

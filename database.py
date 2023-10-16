import logging
import sqlite3
import asyncio
from dataclasses import dataclass
import os
from datetime import datetime

sqlite3.register_adapter(bool, int)
sqlite3.register_adapter(datetime, str)
sqlite3.register_converter("BOOLEAN", lambda v: v != b'0')
sqlite3.register_converter("DATETIME", lambda v: datetime.fromisoformat(v.decode()))

logger = logging.getLogger(__name__)

class Database:
    @dataclass
    class Voting:
        id: int
        title: str
        description: str
        author_id: int
        anonym: bool
        created: datetime
        closed: datetime | None

    @dataclass
    class Vote:
        id: int
        user_id: int
        voting_id: int
        type: bool
        created: datetime

    def __init__(self, path):
        self.path = path
        logger.debug("Иницилизация объекта базы данных")
    
    async def connect_database(self):
        await self.execute_async(self._connect)

    def _connect(self):
        self.connect = sqlite3.connect(self.path, detect_types=sqlite3.
PARSE_DECLTYPES)
        if not os.path.isfile(self.path):
            logger.warning(f"Базы данных {self.path} не существует. В этом случае она будет создана")

        with self.connect:
            cur = self.connect.executescript("""
            CREATE TABLE IF NOT EXISTS votings (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "title" TEXT NOT NULL,
                "description" TEXT NOT NULL,
                "author_id" INTEGER NOT NULL,
                "anonym" BOOLEAN NOT NULL DEFAULT 0,
                "created" DATETIME NOT NULL,
                "closed" DATETIME
            );
            CREATE TABLE IF NOT EXISTS votes (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "user_id" INTEGER NOT NULL,
                "voting_id" INTEGER NOT NULL REFERENCES votings (message_id),
                "type" BOOLEAN NOT NULL,
                "created" DATETIME NOT NULL
            );
            """)
            logger.info("Создание таблиц базы данных если их нет")

    @classmethod
    async def open(cls, path):
        obj = cls(path)
        await obj.connect_database()
        return obj

    def _get(self, query, params):
        cur = self.connect.execute(query, params)
        return cur

    def get(self, query, params):
        cur = self._get(query, params)
        return cur.fetchall()

    def get_one(self, query, params):
        cur = self._get(query, params)
        return cur.fetchone()

    def put(self, query, params):
        with self.connect:
            cur = self.connect.execute(query, params)
            return cur.lastrowid

    async def execute_async(self, method, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: method(*args))

    async def async_get(self, query, params):
        return await self.execute_async(self.get, query, params)

    async def async_get_one(self, query, params):
        return await self.execute_async(self.get_one, query, params)

    async def async_put(self, query, params):
        return await self.execute_async(self.put, query, params)

    async def start_voting(self, title, desc, author_id):
        query = "INSERT INTO votings (title,description,author_id,created) VALUES (?, ?, ?, ?)"
        return await self.async_put(query, (title, desc, author_id, datetime.today()))

    async def close_voting(self, id_):
        query = "UPDATE votings SET closed = ? WHERE id = ?"
        return await self.async_put(query, (datetime.today(), id_))

    async def get_voting(self, id_):
        query = "SELECT * FROM votings WHERE id = ?"
        t = await self.async_get_one(query, (id_,))
        if t is not None:
            return self.Voting(*t)

    async def create_vote(self, user_id, voting_id, type_):
        query = "INSERT INTO votes (user_id,voting_id,type,created) VALUES (?, ?, ?, ?)"
        return  await self.async_put(query, (user_id, voting_id, type_, datetime.today()))

    async def get_vote(self, user_id, voting_id):
        query = "SELECT * FROM votes WHERE user_id = ? AND voting_id = ? ORDER BY id DESC"
        t = await self.async_get_one(query, (user_id, voting_id))
        if t is not None:
            return self.Vote(*t)

    async def get_vote_by_id(self, id_):
        query = "SELECT * FROM votes WHERE id = ?"
        t = await self.async_get_one(query, (id_,))
        if t is not None:
            return self.Vote(*t)

    def __del__(self):
        logger.info("Уничтожение объекта базы данных")

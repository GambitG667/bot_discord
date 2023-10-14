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
        message_id: int
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
        self.connect = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        logger.debug("Иницилизация объекта базы данных")

        if not os.path.isfile(self.path):
            logger.warning(f"Базы данных {self.path} не существует. В этом случае она будет создана")
        
        with self.connect:
            cur = self.connect.executescript("""
            CREATE TABLE IF NOT EXISTS votings (
                "message_id" INTEGER PRIMARY KEY,
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
            self.connect.execute(query, params)

    def start_voting(self, message_id, title, desc, author_id):
        query = "INSERT INTO votings (message_id,title,description,author_id,created) VALUES (?, ?, ?, ?, ?)"
        self.put(query, (message_id, title, desc, author_id, datetime.today()))

    def close_voting(self, message_id):
        query = "UPDATE votings SET closed = ? WHERE message_id = ?"
        self.put(query, (datetime.today(), message_id))

    def vote(self, user_id, voting_id, typ):
        query = "INSERT INTO votes (user_id,voting_id,type,created) VALUES (?, ?, ?, ?)"
        self.put(query, (user_id, voting_id, typ, datetime.today()))

    def get_vote(self, user_id, voting_id):
        query = "SELECT * FROM votes WHERE user_id = ? AND voting_id = ? ORDER BY id DESC"
        t = self.get_one(query, (user_id, voting_id))
        if t is not None:
            return self.Vote(*t)

    def __del__(self):
        self.connect.close()
        logger.info("Уничтожение объекта базы данных")

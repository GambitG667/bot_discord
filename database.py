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

from typing import Callable

class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        logger.debug("Иницилизация объекта базы данных")
    
    async def connect_database(self) -> None:
        await self.execute_async(self._connect)

    def _connect(self) -> None:
        self.connect = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        if not os.path.isfile(self.path):
            logger.warning(f"Базы данных {self.path} не существует. В этом случае она будет создана")

        with self.connect:
            self.connect.executescript("""
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
    async def open(cls, path: str) -> None:
        obj = cls(path)
        await obj.connect_database()
        return obj

    def _get(self, query: str, params) -> None:
        cur = self.connect.execute(query, params)
        return cur

    def get(self, query: str, params) -> None:
        cur = self._get(query, params)
        return cur.fetchall()

    def get_one(self, query: str, params) -> None:
        cur = self._get(query, params)
        return cur.fetchone()

    def put(self, query: str, params) -> None:
        with self.connect:
            cur = self.connect.execute(query, params)
            return cur.lastrowid

    async def execute_async(self, method: Callable, *args: list[any]) -> None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: method(*args))

    async def async_get(self, query: str, params: list[any]) -> None:
        return await self.execute_async(self.get, query, params)

    async def async_get_one(self, query: str, params: list[any]) -> None:
        return await self.execute_async(self.get_one, query, params)

    async def async_put(self, query: str, params: list[any]) -> None:
        return await self.execute_async(self.put, query, params)

    def __del__(self) -> None:
        logger.info("Уничтожение объекта базы данных")

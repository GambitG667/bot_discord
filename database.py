import logging
import sqlite3
import asyncio
import os
from datetime import datetime

sqlite3.register_adapter(bool, int)
sqlite3.register_adapter(datetime, str)
sqlite3.register_converter("BOOLEAN", lambda v: v != b'0')
sqlite3.register_converter("DATETIME", lambda v: datetime.fromisoformat(v.decode()))

logger = logging.getLogger(__name__)

from typing import Callable

class AsyncSQLiteDB:
    def __init__(self, path: str) -> None:
        self.path = path
        self.loop = asyncio.get_event_loop()

        logger.info(f"Иницилизация базы данных ({self.path})")
        if not os.path.isfile(self.path):
            logger.warning(f"Базы данных {self.path} не существует. В этом случае она будет создана")
        self.connect = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)

    async def _is_table_exist(self, table_name: str) -> bool:
        query = "SELECT EXISTS(SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?)"
        ret = (await self.async_fetchone(query, (table_name,)))[0]
        return bool(ret)

    async def _create_table_async(self, query: str, table_name: str) -> None:
        logger.debug(f"Проверка таблицы {table_name} на наличие в базе данных")
        if not (await self._is_table_exist(table_name)):
            logger.warning(f"Таблицы \"{table_name}\" нет в базе. Она будет создана")
        await self.execute_async(self.async_operate, query)

    async def _create_votings_table(self) -> None:
        table_name = "votings"
        query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "title" TEXT NOT NULL,
            "description" TEXT NOT NULL,
            "author_id" INTEGER NOT NULL,
            "anonym" BOOLEAN NOT NULL DEFAULT 0,
            "created" DATETIME NOT NULL,
            "closed" DATETIME
        );"""
        await self._create_table_async(query, table_name)

    async def _create_votes_table(self) -> None:
        table_name = "votes"
        query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "user_id" INTEGER NOT NULL,
            "voting_id" INTEGER NOT NULL,
            "type" BOOLEAN NOT NULL,
            "created" DATETIME NOT NULL,
            FOREIGN KEY (voting_id) REFERENCES votings (id)
        )"""
        await self._create_table_async(query, table_name)

    async def _create_petitions_table(self) -> None:
        table_name = "petitions"
        query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "title" TEXT NOT NULL,
            "description" TEXT NOT NULL,
            "author_id" INTEGER NOT NULL,
            "anonym" BOOLEAN NOT NULL DEFAULT 0,
            "created" DATETIME NOT NULL,
            "closed" DATETIME
        );"""
        await self._create_table_async(query, table_name)

    async def _create_signs_table(self) -> None:
        table_name = "signs"
        query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "user_id" INTEGER NOT NULL,
            "petition_id" INTEGER NOT NULL,
            "created" DATETIME NOT NULL,
            FOREIGN KEY (petition_id) REFERENCES petitions (id)
        )"""
        await self._create_table_async(query, table_name)

    async def _create_voting_life_table(self) -> None:
        table_name = "voting_life"
        query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
            "voting_id" INTEGER PRIMARY KEY,
            "channel_id" INTEGER NOT NULL,
            "death" DATETIME NOT NULL,
            FOREIGN KEY (voting_id) REFERENCES votings (id)
        )"""
        await self._create_table_async(query, table_name)

    async def _create_petition_life_table(self) -> None:
        table_name = "petition_life"
        query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
            "petition_id" INTEGER PRIMARY KEY,
            "channel_id" INTEGER NOT NULL,
            "death" DATETIME NOT NULL,
            FOREIGN KEY (petition_id) REFERENCES petitions (id)
        )"""
        await self._create_table_async(query, table_name)

    async def _create_tables(self) -> None:
        await self._create_votings_table()
        await self._create_votes_table()
        await self._create_voting_life_table()
        await self._create_petitions_table()
        await self._create_signs_table()
        await self._create_petition_life_table()
        logger.debug("Все таблицы были проверены и/или созданы")

    def _get(self, query: str, params: tuple[any] | None = None) -> sqlite3.Cursor:
        if params is None:
            cur = self.connect.execute(query)
        else:
            cur = self.connect.execute(query, params)
        return cur

    def fetchall(self, query: str, params: tuple[any] | None = None) -> list[any]:
        cur = self._get(query, params)
        return cur.fetchall()

    def fetchone(self, query: str, params: tuple[any] | None = None) -> any:
        cur = self._get(query, params)
        return cur.fetchone()

    def operate(self, query: str, params: tuple[any] | None = None) -> int | None:
        if params is None:
            cur = self.connect.execute(query)
        else:
            cur = self.connect.execute(query, params)
            
        self.connect.commit()
        return cur.lastrowid

    async def execute_async(self, method: Callable, query: str, params: tuple[any] | None = None) -> any:
        return await self.loop.run_in_executor(None, lambda: method(query, params))

    async def async_fetchall(self, query: str, params: tuple[any] | None = None) -> list[any]:
        return await self.execute_async(self.fetchall, query, params)

    async def async_fetchone(self, query: str, params: tuple[any] | None = None) -> any:
        return await self.execute_async(self.fetchone, query, params)

    async def async_operate(self, query: str, params: tuple[any] | None = None) -> int:
        return await self.execute_async(self.operate, query, params)
    
    def _sync_close(self) -> None:
        self.connect.close()
        logger.info("База данных закрыта")

    async def close(self) -> None:
        await self.loop.run_in_executor(None, self._sync_close)

    def __del__(self) -> None:
        self.loop.run_until_complete(self.close())
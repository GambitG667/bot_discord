import logging
import sqlite3
import os

logger = logging.getLogger(__name__)

class Database:
    databasePath = "database.db"
    if not os.path.isfile(databasePath):
        logger.warning(f"Базы данных {databasePath} не существует. В этом случае она будет создана")

    connection = sqlite3.connect(databasePath)
    cursor = connection.cursor()
    logger.info("Успешное подключение к базе данных")

    queries = {
        "sv": "INSERT INTO votings (message_id, title, description, author_id) VALUES (?, ?, ?, ?)",
        "stopv": "UPDATE votings SET is_open = 0 WHERE message_id = ?",
        "vote": "INSERT INTO votes (user_id, voting_id, type) VALUES (?, ?, ?)",
        "revote": "UPDATE votes SET type = ? WHERE user_id = ? AND voting_id = ?",
        "get_vote": "SELECT * FROM votes WHERE user_id = ? AND voting_id = ?"
    }

    # Если база данных была только что создана, выполнится условие на создание таблиц
    with connection:
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS votings (
            message_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            is_open INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER NOT NULL,
            voting_id INTEGER NOT NULL REFERENCES votings (message_id),
            type INTEGER NOT NULL CHECK(type >= 0 AND type <= 1),
            PRIMARY KEY(user_id, voting_id)
        );
        """)
    
    @classmethod
    def vote(cls, user_id: int, voting_id: int, type_: bool | int):
        with cls.connection:
            cls.cursor.execute(cls.queries["get_vote"], (user_id, voting_id))
            t = cls.get_vote_index(user_id, voting_id, 2)
            if t is None:
                cls.cursor.execute(cls.queries["vote"], (user_id, voting_id, int(type_)))
                logger.debug(f"Создание запроса на добавление в таблицу votes параметров: {user_id=}, {voting_id=}, {type_=}")
            else:
                cls.cursor.execute(cls.queries["revote"], (int(type_), user_id, voting_id))
                logger.debug(f"Создание запроса на изменение таблицы votes с полями {user_id=}, {voting_id} параметров: {type_=}")

    @classmethod
    def start_voting(cls, message_id: int, title: str, description: str, author_id: int):
        with cls.connection:
            cls.cursor.execute(cls.queries["sv"], (message_id, title, description, author_id))
            logger.debug(f"Создание запроса на добавление в таблицу votings параметров: {message_id=}, {title=}, {description=}, {author_id=}")
    
    @classmethod
    def stop_voting(cls, message_id):
        with cls.connection:
            print(type(message_id))
            cls.cursor.execute(cls.queries["stopv"], (message_id,))
            logger.debug(f"Создание запроса на изменение таблицы votings с полями {message_id=} параметров: is_open=False")

    @classmethod
    def get_vote(cls, user_id, voting_id):
        with cls.connection:
            cls.cursor.execute(cls.queries["get_vote"], (user_id, voting_id))
            logger.debug(f"Создание запроса на строку в таблицу votes c параметрами: {user_id=}, {voting_id=}")
            return cls.cursor.fetchone()

    @classmethod
    def get_vote_index(cls, user_id, voting_id, index):
        fetch = cls.get_vote(user_id, voting_id)
        if fetch:
            return fetch[index]
        return None

    @classmethod
    def close(cls):
        logger.info("Подключение к базе данных закрыто")
        csl.connection.close()

import logging
from argparser import args

# Создаём логгер для root дериктории
def setup_logger() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logging.getLogger("aiosqlite").setLevel(logging.INFO)
    logging.getLogger("disnake").setLevel(logging.WARNING)
    
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] - {name}: {message}",
        "%d-%m-%Y %H:%M:%S",
        style="{"
    )

    if args["out"]:
        fileHandler = logging.FileHandler("bot.log", encoding="utf-8")
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    if args["out_file"]:
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)

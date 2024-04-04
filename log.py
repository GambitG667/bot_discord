import logging
from argparser import args

# Создаём логгер для root дериктории
def setup_logger() -> None:
    logger = logging.getLogger()
    level = None
    match args.logger_level:
        case "DEBUG":
            level = logging.DEBUG
        case "INFO":
            level = logging.INFO
        case "WARNING":
            level = logging.WARNING
        case "ERROR":
            level = logging.ERROR
        case "CRITICAL":
            level = logging.CRITICAL

    logger.setLevel(level)

    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.getLogger("aiosqlite").setLevel(logging.INFO)
    logging.getLogger("disnake").setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] - {name}: {message}",
        "%d-%m-%Y %H:%M:%S",
        style="{"
    )

    if args.out:
        fileHandler = logging.FileHandler("bot.log", encoding="utf-8")
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    if args.out_file:
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)

    logger.debug("Логгер установлен")
import logging

# Создаём логгер для root дериктории
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
            "[{asctime}] [{levelname:<8}] - {name}: {message}",
            "%d-%m-%Y %H:%M:%S",
            style="{"
                                  )

    fileHandler = logging.FileHandler("bot.log")
    fileHandler.setFormatter(formatter)

    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)

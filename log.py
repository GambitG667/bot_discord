import logging

def setup_logger(main):
    logger = logging.getLogger(main)
    logger.setLevel(logging.INFO)
    
    dt_fmt = '%Y-%m-%d %H:%M:%S' 
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    fileHandler = logging.FileHandler("log.txt")
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    return logger

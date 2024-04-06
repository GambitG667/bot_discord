import argparse
import logging
import os
from dotenv import load_dotenv
load_dotenv()

class ArgsNamespace(argparse.Namespace):
    database: str
    out: bool
    out_file: bool
    logger_level: str
    token: str
    error_webhook: int
    info_webhook: int

argparser = argparse.ArgumentParser(description="Главный файл для запуска бота")
argparser.add_argument("--database", "-d", metavar="*.db", type=str, default="database.db", help="Имя или путь до базы данных. Если базы нет, она будет создана")
argparser.add_argument("--out", action=argparse.BooleanOptionalAction, default=True, help="Логирование в консоли (по умолчанию включено)")
argparser.add_argument("--out-file", action=argparse.BooleanOptionalAction, default=True, help="Логирование в файле (по умолчанию включено)")
argparser.add_argument("--logger-level", "-l", choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), default="INFO", help="Уровень логирования")
argparser.add_argument("--token", "-t", metavar="BOT_TOKEN", type=str, default=os.getenv("BOT_TOKEN"), help="Использует данный токен или переменную окр. BOT_TOKEN")
argparser.add_argument("--error-webhook", "-e", metavar="BOT_ERROR_WEBHOOK_ID", type=int, default=os.getenv("BOT_ERROR_WEBHOOK_ID"), help="Использует вебхук для исключений или переменную окр. BOT_ERROR_WEBHOOK_ID или игнорирует")
argparser.add_argument("--info-webhook", "-i", metavar="BOT_INFO_WEBHOOK_ID", type=int, default=os.getenv("BOT_INFO_WEBHOOK_ID"), help="Использует вебхук для информирования или переменную окр. BOT_INFO_WEBHOOK_ID или игнорирует")

args = argparser.parse_args(namespace=ArgsNamespace())
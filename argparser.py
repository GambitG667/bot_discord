import argparse
import logging

argparser = argparse.ArgumentParser(description="Главный файл для запуска бота")
argparser.add_argument("--database", "-d", metavar="*.db", type=str, default="database.db", help="Имя или путь до базы данных. Если базы нет, она будет создана")
argparser.add_argument("--out", action=argparse.BooleanOptionalAction, default=True, help="Логирование в консоли (по умолчанию включено)")
argparser.add_argument("--out-file", action=argparse.BooleanOptionalAction, default=True, help="Логирование в файле (по умолчанию включено)")
argparser.add_argument("--logger-level", "-l", choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), default="INFO", help="Уровень логирования")
argparser.add_argument("--token", "-t", metavar="TOKEN_NAME", type=str, default="TOKEN", help="Имя токена в окружении")
argparser.add_argument("--webhook", "-w", metavar="WEBHOOK_ID", type=int, default=None, help="При указании ключа бот будет использовать данный вебхук для отправки ошибок в канал.")

args = argparser.parse_args()
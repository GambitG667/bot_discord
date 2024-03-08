import argparse

argparser = argparse.ArgumentParser(description="Главный файл для запуска бота")
argparser.add_argument("--database", "-d", nargs=1, metavar="*.db", type=str, default="database.db", help="Имя или путь до базы данных. Если базы нет, она будет создана")
argparser.add_argument("--out", action=argparse.BooleanOptionalAction, default=True, help="Логирование в консоли (по умолчанию включено)")
argparser.add_argument("--out-file", action=argparse.BooleanOptionalAction, default=True, help="Логирование в файле (по умолчанию включено)")

args = vars(argparser.parse_args())
#print(args)
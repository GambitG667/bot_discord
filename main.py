import disnake
from disnake.ext import commands
from secret import TOKEN
import logging
from log import setup_logger
setup_logger()

from commands import commandList
from database import Database

logger = logging.getLogger(__name__)
logger.debug("Логгер установлен")

# Бот, который работает только с командами приложения
bot = commands.InteractionBot(intents=disnake.Intents.all())

# Парсим команды c помощью цикл.
for command in commandList:
    logger.debug(f"Регистрация комманды {command.name}")
    bot.add_slash_command(command)

@bot.event
async def on_ready():
    logger.info(f"Бот {bot.user} готов!")
    bot.db = await Database.open("database.db")

@bot.event
async def on_disconnect():
    logger.info(f"Соединение прервано")

bot.run(TOKEN)

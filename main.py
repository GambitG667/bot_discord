import disnake
from disnake.ext import commands
from secret import TOKEN
import logging

from commands import commandList
from log import setup_logger

setup_logger()
logger = logging.getLogger(__name__)
# Иногда почему-то disnake начинает засарять терминал своими логами
logging.getLogger("disnake").setLevel(logging.WARNING)

# Бот, который работает только с командами приложения
bot = commands.InteractionBot(intents=disnake.Intents.all())

# Парсим команды c помощью цикл.
for command in commandList:
    logger.debug(f"Регистрация комманды {command.name}")
    bot.add_slash_command(command)

@bot.event
async def on_ready():
    logger.info(f"Бот {bot.user} готов!")

bot.run(TOKEN)

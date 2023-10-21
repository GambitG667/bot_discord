import disnake
from disnake.ext import commands
from config import TOKEN
import logging
from log import setup_logger
setup_logger()

from commons import Commons
from admins import Admins
from database import Database

logger = logging.getLogger(__name__)
logger.debug("Логгер установлен")

# Бот, который работает только с командами приложения
bot = commands.InteractionBot(intents=disnake.Intents.all())

logger.debug(f"Регистрация кога common")
bot.add_cog(Commons())
logger.debug(f"Регистрация кога admins")
bot.add_cog(Admins())

@bot.event
async def on_ready():
    logger.info(f"Бот {bot.user} готов!")
    bot.db = await Database.open("database.db")

bot.run(TOKEN)

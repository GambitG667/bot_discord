import disnake
from disnake.ext import commands
from config import TOKEN
import logging
from log import setup_logger
setup_logger()

from voting import Voting
from database import Database
from commands import Commons

logger = logging.getLogger(__name__)
logger.debug("Логгер установлен")

# Бот, который работает только с командами приложения
bot = commands.InteractionBot(intents=disnake.Intents.all())

logger.debug(f"Регистрация кога common")
bot.add_cog(Commons())

@bot.event
async def on_ready():
    logger.info(f"Бот {bot.user} готов!")
    bot.voting = Voting(await Database.open("database.db"))

bot.run(TOKEN)

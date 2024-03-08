import disnake
from disnake.ext import commands
from config import TOKEN
import logging
from argparser import args
from log import setup_logger
setup_logger()

from voting import Voting
from database import Database
from commands import Commons

logger = logging.getLogger(__name__)
logger.debug("Логгер установлен")

# Бот, который работает только с командами приложения
bot = commands.InteractionBot(intents=disnake.Intents.all())

logger.debug(f"Регистрация кога Commons")
bot.add_cog(Commons())

@bot.event
async def on_ready() -> None:
    logger.info(f"Бот {bot.user} готов!")
    bot.voting = Voting(await Database.open(args["database"][0]))

@bot.event
async def on_slash_command_error(inter: disnake.CommandInter, error: commands.CommandError) -> None:
    logger.error(f"Команда [{inter.application_command.qualified_name}] для {inter.author.display_name} создала ошибку: {error}")
    # if not inter.response.is_done():
        # await inter.response.defer()
    # if isinstance(error, commands.CommandInvokeError):
    #     await inter.edit_original_response("На данный момент бот работает очень плохо. Извините за неудобства.", ephemeral=True)

@bot.event
async def on_slash_command(inter: disnake.CommandInter) -> None:
    params = (f"{k}: {v}" for k, v in inter.filled_options.items())
    logger.info(f"{inter.author.display_name} запросил комманду [{inter.application_command.qualified_name}] с параметрами {', '.join(params)}")

@bot.event
async def on_slash_command_completion(inter: disnake.CommandInter) -> None:
    params = (f"{k}: {v}" for k, v in inter.filled_options.items())
    logger.info(f"Для {inter.author.display_name} команда [{inter.application_command.qualified_name}] была выполнена успешно с параметрами {', '.join(params)}")

bot.run(TOKEN)

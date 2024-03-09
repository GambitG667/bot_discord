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
    command = inter.application_command
    if command and command.has_error_handler():
        return

    cog = command.cog
    if cog and cog.has_slash_error_handler():
        return
    
    logger.error(
        f"При выполнении команды [{inter.application_command.qualified_name}] для {inter.author.display_name} проигнорирована ошибка:",
        exc_info=(type(error), error, error.__traceback__)
    )

@bot.event
async def on_slash_command(inter: disnake.CommandInter) -> None:
    params = (f"{k}: {v}" for k, v in inter.filled_options.items())
    logger.info(f"{inter.author.display_name} запросил комманду [{inter.application_command.qualified_name}] с параметрами {', '.join(params)}")

@bot.event
async def on_slash_command_completion(inter: disnake.CommandInter) -> None:
    params = (f"{k}: {v}" for k, v in inter.filled_options.items())
    logger.info(f"Для {inter.author.display_name} команда [{inter.application_command.qualified_name}] была выполнена успешно с параметрами {', '.join(params)}")

bot.run(TOKEN)

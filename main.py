import disnake
from disnake.ext import commands
import logging
from argparser import args
from log import setup_logger
import os
from dotenv import load_dotenv
load_dotenv()
setup_logger()

from voting import VotingMaker
from database import Database
from commands import Commons

token_name: str = args.token
token = os.getenv(token_name)
if token is None:
    raise ValueError(f"Токен {token_name} не обнаружен")

logger = logging.getLogger(__name__)

# Бот, который работает только с командами приложения
class Bot(commands.InteractionBot):
    def __init__(self) -> None:
        super().__init__(intents=disnake.Intents.all())

        logger.debug(f"Регистрация кога Commons")
        self.add_cog(Commons())

    async def on_ready(self) -> None:
        logger.info(f"Бот {bot.user} готов!")
        self.voting = VotingMaker(await Database.open(args.database))

    async def on_slash_command_error(self, inter: disnake.CommandInter, error: commands.CommandError) -> None:
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

    async def on_slash_command(self, inter: disnake.CommandInter) -> None:
        params = list(f"{k}: {v}" for k, v in inter.filled_options.items())
        t = [f"{inter.author.display_name} запросил комманду [{inter.application_command.qualified_name}]"]
        if len(params) != 0:
            t.append(f"с параметрами {', '.join(params)}")
        logger.info(" ".join(t))

    async def on_slash_command_completion(self, inter: disnake.CommandInter) -> None:
        params = list(f"{k}: {v}" for k, v in inter.filled_options.items())
        t = [f"Для {inter.author.display_name} команда [{inter.application_command.qualified_name}] была выполнена успешно"]
        if len(params) != 0:
            t.append(f"с параметрами {', '.join(params)}")
        logger.info(" ".join(t))

bot = Bot()
bot.run(token)
import disnake
from disnake.ext import commands
from .voting import voting
import logging

logger = logging.getLogger(__name__)

class Commons(commands.Cog):
    def __init__(self):
        for command in self.get_slash_commands():
            logger.debug(f"В коге {self.qualified_name} зарегестрирована комманда {command.name}")

    voting = voting

import disnake
from disnake.ext import commands

class Admins(commands.Cog):
    def __init__(self):
        for command in self.get_slash_commands():
            logger.debug(f"В коге {self.qualified_name} зарегестрирована комманда {command.name}")

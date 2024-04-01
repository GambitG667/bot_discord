from __future__ import annotations
import disnake
from disnake.ext import commands

import logging
logger = logging.getLogger(__name__)

from commands import _voting_id, _petition_id

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Bot

class Admins(commands.Cog):
    def __init__(self) -> None:
        for command in self.get_slash_commands():
            command.body.dm_permission = False
            command.body._default_member_permissions = disnake.Permissions(administrator=True).value    # очень печально об этом говорить
            logger.debug(f"В коге {self.qualified_name} зарегестрирована комманда {command.name}")
        
    @commands.slash_command(
        name="бд"
    )
    async def data_base(self, inter: disnake.CommandInter, *args) -> None:
        pass

    @data_base.sub_command_group(
        name="голосование"
    )
    async def voting(self, inter: disnake.CommandInter, *args) -> None:
        pass

    @voting.sub_command(
            name="удалить",
            description="Удаляет голосование (оставляет пустой след поэтому могут возникнуть вопросы)"
    )
    async def delete(self, inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        bot: Bot = inter.bot
        await bot.voting.delete_voting(id_)
        await inter.send("Команда выполнена успешно", ephemeral=True)

    @data_base.sub_command_group(
        name="петиция"
    )
    async def petition(self, inter: disnake.CommandInter, *args) -> None:
        pass

    @petition.sub_command(
            name="удалить",
            description="Удаляет петицию (см \"бд голосование удалить\")"
    )
    async def delete(self, inter: disnake.CommandInter, id_: int = _petition_id) -> None:
        bot: Bot = inter.bot
        await bot.voting.delete_petition(id_)
        await inter.send("Команда выполнена успешно", ephemeral=True)
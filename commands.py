from __future__ import annotations
import disnake
from disnake.ext import commands
from datetime import datetime

from views import *
from modals import *
from embeds import *

import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

Id = commands.Param(name="id", ge=1)

async def check_voting(inter: disnake.CommandInter, id_) -> bool:
    voting = await inter.bot.voting.get_voting(id_)
    if voting:
        return True

class Commons(commands.Cog):
    def __init__(self) -> None:
        for command in self.get_slash_commands():
            logger.debug(f"В коге {self.qualified_name} зарегестрирована комманда {command.name}")

    @commands.slash_command(
            name="голосование",
            description="Команда для работы с голосованиями",
            dm_permition=False
    )
    async def voting(inter: disnake.CommandInter, *args) -> None:
        pass

    @voting.sub_command(
            name="создать",
            description="Создать голосование"
    )
    async def create(inter: disnake.CommandInter, anonym: bool = False) -> None:
        await inter.response.send_modal(modal=CreateModal(anonym))

    @voting.sub_command(
            name="отобразить",
            description="Отображает голосование по его id"
    )
    async def show(inter: disnake.CommandInter, id_ = Id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_voting(inter, id_):
            voting = await inter.bot.voting.get_voting(id_)
            embed = VotingEmbed(
                    inter.bot.get_user(voting.author_id),
                    voting.title,
                    voting.description,
                    id_,
                    voting.created,
                    voting.anonym
            )
            await inter.edit_original_response(embed=embed, view=VotingView(id_))
        else:
            await inter.edit_original_response(f"Голосование {id_} не найдено")

    @voting.sub_command(
        name="результаты",
        description="Отображает результаты голосования"
    )
    async def results(inter: disnake.CommandInter, id_ = Id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_voting(inter, id_):
            voting = await inter.bot.voting.get_voting(id_)
            against, for_ = await inter.bot.voting.get_votes(id_)
            time = voting.closed if voting.closed else datetime.today()
            embed = ResultsEmbed(
                inter.bot.get_user(voting.author_id),
                voting.title,
                id_,
                time,
                for_,
                against,
                voting.anonym
            )
            await inter.edit_original_response(embed=embed)
        else:
            await inter.edit_original_response(f"Голосование {id_} не найдено")

    @voting.sub_command(
        name="история",
        description="Отображает список всех голосов"
    )
    async def votingList(inter: disnake.CommandInter, id_ = Id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_voting(inter, id_):
            view = LineView(inter, id_)
            view, embed = (await view.change(0))
            if view is not None:
                await inter.edit_original_response(content=None, view=view, embed=embed)
        else:
            await inter.edit_original_response(f"Голосование {id_} не найдено")
import disnake
from disnake.ext import commands
from datetime import datetime

from views import *
from modals import *
from embeds import *

import logging
logger = logging.getLogger(__name__)

Id = commands.Param(name="id", ge=1)

class Commons(commands.Cog):
    def __init__(self):
        for command in self.get_slash_commands():
            logger.debug(f"В коге {self.qualified_name} зарегестрирована комманда {command.name}")

    @commands.slash_command(
            name="голосование",
            description="Команда для работы с голосованиями",
            dm_permition=False
    )
    async def voting(inter, *args):
        pass

    @voting.sub_command(
            name="создать",
            description="Создать голосование"
    )
    async def create(inter, anonym: bool = False):
        await inter.response.send_modal(modal=CreateModal(anonym))

    @voting.sub_command(
            name="отобразить",
            description="Отображает голосование по его id"
    )
    async def show(inter, id_ = Id):
        voting = await inter.bot.voting.get_voting(id_)
        if voting:
            embed = VotingEmbed(
                    inter.bot.get_user(voting.author_id),
                    voting.title,
                    voting.description,
                    id_,
                    voting.created,
                    voting.anonym
            )
            await inter.send(embed=embed, view=VotingView(id_), ephemeral=True)
        else:
            await inter.send(f"Голосование {id_} не найдено", ephemeral=True)
        logger.info(f"{inter.author.display_name} отобразил голосование {id_}")

    @voting.sub_command(
        name="результаты",
        description="Отображает результаты голосования"
    )
    async def results(inter, id_ = Id):
        voting = await inter.bot.voting.get_voting(id_)
        if voting:
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
            await inter.send(embed=embed, ephemeral=True)
        else:
            await inter.send(f"Голосование {id_} не найдено", ephemeral=True)
        logger.info(f"{inter.author.display_name} запросил результаты голосования {id_}")
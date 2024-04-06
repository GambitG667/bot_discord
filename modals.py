from __future__ import annotations
import disnake
from disnake.ext import commands
from datetime import datetime, timedelta

from views import *
from embeds import *

import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from activity_tasks import ActivityTasks

class AbsTitleAndDescModal(disnake.ui.Modal):
    def __init__(self, title: str, genitive_case: str, custom_id: str, anonym: bool) -> None:
        self.anonym = anonym
        comp = [
            disnake.ui.TextInput(
                label="Заголовок",
                placeholder=f"Напишите тему {genitive_case}",
                custom_id="title",
                style=disnake.TextInputStyle.short,
                max_length=20
            ),
            disnake.ui.TextInput(
                label="Описание",
                placeholder=f"Напишите полное описание {genitive_case}",
                custom_id="description",
                style=disnake.TextInputStyle.long
            )
        ]
        super().__init__(
            title=title,
            custom_id=custom_id,
            components=comp
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        self.title = inter.text_values["title"]
        self.desc = inter.text_values["description"]

class CreateVotingModal(AbsTitleAndDescModal):
    def __init__(self, anonym: bool, channel_id: int, td: timedelta) -> None:
        super().__init__(
            title="Голосование",
            genitive_case="голосования",
            custom_id="voting",
            anonym=anonym
        )
        self.channel_id = channel_id
        self.td = td

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await super().callback(inter)
        bot: Bot = inter.bot
        voting = await bot.voting.start_voting(self.title, self.desc, inter.author.id, self.anonym)
        if self.td.total_seconds() != 0:
            task: ActivityTasks = inter.bot.get_cog("ActivityTasks")
            await task.create_voting_life(voting.id, self.channel_id, self.td)
            
        view = VotingView(voting.id)

        embed = ActivityEmbed(
            inter,
            inter.author,
            voting
        )

        logger.info(f"{inter.author.name} начал голосование №{voting.id}: {self.title}")
        await bot.send_info_webhook(content=f"{inter.author.mention} начал голосование №{voting.id}: {self.title}")
        await inter.send("@everyone", embed=embed, view=view)

class CreatePetitionModal(AbsTitleAndDescModal):
    def __init__(self, anonym: bool, channel_id: int, td: timedelta) -> None:
        super().__init__(
            title="Петиция",
            genitive_case="петиции",
            custom_id="petition",
            anonym=anonym
        )
        self.channel_id = channel_id
        self.td = td

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await super().callback(inter)
        bot: Bot = inter.bot
        petition = await bot.voting.start_petition(self.title, self.desc, inter.author.id, self.anonym)
        if self.td.total_seconds() != 0:
            task: ActivityTasks = inter.bot.get_cog("ActivityTasks")
            await task.create_petition_life(petition.id, self.channel_id, self.td)
        view = PetitionView(petition.id)

        embed = ActivityEmbed(
            inter,
            inter.author,
            petition
        )

        logger.info(f"{inter.author.name} начал петицию №{petition.id}: {self.title}")
        await bot.send_info_webhook(content=f"{inter.author.mention} начал петицию №{petition.id}: {self.title}")
        await inter.send("@everyone", embed=embed, view=view)
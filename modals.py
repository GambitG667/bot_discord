from __future__ import annotations
import disnake
from disnake.ext import commands
from datetime import datetime

from views import *
from embeds import *

import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

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
    def __init__(self, anonym: bool) -> None:
        super().__init__(
            title="Голосование",
            genitive_case="голосования",
            custom_id="voting",
            anonym=anonym
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await super().callback(inter)
        bot: Bot = inter.bot
        voting = await bot.voting.start_voting(self.title, self.desc, inter.author.id, self.anonym)
        view = VotingView(voting.id)

        embed = ActivityEmbed(
            inter.author,
            voting
        )

        logger.info(f"{inter.author.display_name} начал голосование №{voting.id}: {self.title}")
        await inter.send("@everyone", embed=embed, view=view)

class CreatePetitionModal(AbsTitleAndDescModal):
    def __init__(self, anonym: bool) -> None:
        super().__init__(
            title="Петиция",
            genitive_case="петиции",
            custom_id="petition",
            anonym=anonym
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await super().callback(inter)
        bot: Bot = inter.bot
        petition = await bot.voting.start_petition(self.title, self.desc, inter.author.id, self.anonym)
        view = PetitionView(petition.id)

        embed = ActivityEmbed(
            inter.author,
            petition
        )

        logger.info(f"{inter.author.display_name} начал петицию №{petition.id}: {self.title}")
        await inter.send("@everyone", embed=embed, view=view)
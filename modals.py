import disnake
from disnake.ext import commands
from datetime import datetime

from views import *
from embeds import *

import logging
logger = logging.getLogger(__name__)

class CreateModal(disnake.ui.Modal):
    def __init__(self, anonym):
        self.anonym = anonym
        comp = [
            disnake.ui.TextInput(
                label = "Заголовок",
                placeholder = "Напишите тему голосования",
                custom_id = "title",
                style=disnake.TextInputStyle.short,
                max_length=20
            ),
            disnake.ui.TextInput(
                label = "Описание",
                placeholder = "Напишите полное описание голосования",
                custom_id = "description",
                style=disnake.TextInputStyle.long
            )
        ]
        super().__init__(
            title="Голосование",
            custom_id="voting",
            components=comp
        )

    async def callback(self, inter):
        title = inter.text_values["title"]
        desc = inter.text_values["description"]

        voting_id = await inter.bot.voting.start_voting(title, desc, inter.author.id, self.anonym)
        view = VotingView(voting_id)

        embed = VotingEmbed(
            inter.author,
            title,
            desc,
            voting_id,
            datetime.today(),
            self.anonym
        )

        logger.info(f"{inter.author.display_name} начал голосование: {title} => {desc}")
        await inter.send("@everyone", embed=embed, view=view)
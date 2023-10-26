import disnake
from disnake.ext import commands
import logging

from embeds import *

logger = logging.getLogger(__name__)

class VotingView(disnake.ui.View):
    def __init__(self, voting_id,  timeout = None):
        super().__init__(timeout=timeout)
        self.voting_id = voting_id

    async def vote(self, inter, type_, label):
        user = inter.author
        vote = await inter.bot.voting.get_vote(inter.author.id, self.voting_id)
        voting = await inter.bot.voting.get_voting(self.voting_id)
        t = None
        if vote is not None:
            t = vote.type

        if voting.closed is not None:
            await inter.send(f"Голосование закрыто", ephemeral=True)
            return

        if t == type_:
            await inter.send(f"Вы уже проголосовали за {label}", ephemeral=True)
        else:
            logger.info(f"{user.display_name} прологосовал за \"{label}\"")

            await inter.send(f"Вы проголосовали за {label}", ephemeral=True)
            await inter.bot.voting.create_vote(inter.author.id, self.voting_id, type_)

    @disnake.ui.button(label="Согласен", style=disnake.ButtonStyle.green)
    async def confirm(self, button, inter):
        await self.vote(inter, True, button.label)

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cancel(self, button, inter):
        await self.vote(inter, False, button.label)

    @disnake.ui.button(label="Окончить голосование", style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button, inter):
        voting = await inter.bot.voting.get_voting(self.voting_id)
        if voting.closed is not None:
            await inter.send("Голосование уже было закрыто", ephemeral=True)
            return

        if inter.permissions.administrator or inter.author.id == self.author.id:
            await inter.bot.voting.close_voting(self.voting_id)
            logger.info(f"{inter.author.display_name} окончил голосование")
            voting = await inter.bot.voting.get_voting(self.voting_id)
            against, for_ = await inter.bot.voting.get_votes(self.voting_id)
            embed = ResultsEmbed(
                inter.bot.get_user(voting.author_id),
                voting.title,
                self.voting_id,
                voting.closed,
                for_,
                against,
                voting.anonym
            )
            await inter.send(embed=embed)
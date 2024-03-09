from __future__ import annotations
import disnake
from disnake.ext import commands
import logging

from embeds import *

logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from voting import Voting

class VotingView(disnake.ui.View):
    def __init__(self, voting_id,  timeout = None) -> None:
        super().__init__(timeout=timeout)
        self.voting_id = voting_id

    async def vote(self, inter: disnake.MessageInteraction, type_, label: str) -> None:
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
    async def confirm(self, button, inter: disnake.MessageInteraction) -> None:
        await self.vote(inter, True, button.label)

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        await self.vote(inter, False, button.label)

    @disnake.ui.button(label="Окончить голосование", style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
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

class AbsList(disnake.ui.View):
    def __init__(self, inter: disnake.MessageInteraction, index: int = 1, *, timeout: float | None = None) -> None:
        self.old_inter = inter
        self.index = index
        super().__init__(timeout=timeout)

    async def change(self, offset: int) -> None:
        self.index += offset
        self.next.disabled = False
        self.previous.disabled = False

    async def disable_buttons(self, len_: int) -> None:
        if len_ != 21:
            self.next.disabled = True
        if self.index == 1:
            self.previous.disabled = True
    
    @disnake.ui.button(label="Предыдущий", style=disnake.ButtonStyle.gray)
    async def previous(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        embed = await self.change(-1)
        await self.old_inter.edit_original_response(content=None, embed=embed, view=self)

    @disnake.ui.button(label="Следующий", style=disnake.ButtonStyle.gray)
    async def next(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        embed = await self.change(1)
        await self.old_inter.edit_original_response(content=None, embed=embed, view=self)

class LineVotesView(AbsList):
    def __init__(self, inter: disnake.MessageInteraction, voting_id: int, index: int = 1) -> None:
        self.voting_id = voting_id
        super().__init__(inter, index, timeout=None)

    async def change(self, offset: int) -> VotesListEmbed | None:
        await super().change(offset)
        voting: Voting.Voting  = await self.old_inter.bot.voting.get_voting(self.voting_id)
        votes: list[Voting.VoteWithIndex] = await self.old_inter.bot.voting.get_votes_list(self.voting_id, (self.index - 1) * 20)
        await self.disable_buttons(len(votes))

        if voting.anonym and not self.old_inter.permissions.administrator:
            await self.old_inter.edit_original_response("Данное голосование является аннонимным", view=None)
            return

        if len(votes) == 0:
            await self.old_inter.edit_original_response("Данное голосование пока что не имеет истории", view=None)
            return

        embed = VotesListEmbed(
            self.old_inter.bot,
            votes,
            self.voting_id,
            voting.anonym
        )
        return embed
    
class LineVotingsView(AbsList):
    async def change(self, offset: int) -> VotingsListEmbed | None:
        await super().change(offset)
        votings: list[Voting.VotingWithIndex] = await self.old_inter.bot.voting.get_votings_list((self.index - 1) * 20)
        await self.disable_buttons(len(votings))

        if len(votings) == 0:
            await self.old_inter.edit_original_response("Пока что нет голосований", view=None)
            return
        
        embed = VotingsListEmbed(
            self.old_inter.bot,
            votings
        )
        return embed
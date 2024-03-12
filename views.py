from __future__ import annotations
import disnake
from disnake.ext import commands
import logging

from embeds import *

logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Bot

class VotingView(disnake.ui.View):
    def __init__(self, voting_id: int, timeout: float | None = None) -> None:
        super().__init__(timeout=timeout)
        self.voting_id = voting_id

    async def vote(self, inter: disnake.MessageInteraction, type_: bool, button: disnake.Button) -> None:
        user = inter.author
        bot: Bot = inter.bot
        vote = await bot.voting.get_vote(inter.author.id, self.voting_id)
        voting = await bot.voting.get_voting(self.voting_id)
        t: bool | None = None
        if vote is not None:
            t = vote.type

        if voting.closed is not None:
            await inter.send(f"Голосование закрыто", ephemeral=True)
            return

        if t == type_:
            await inter.send(f"Вы уже проголосовали за {button.label}", ephemeral=True)
        else:
            logger.info(f"{user.display_name} прологосовал за \"{button.label}\" в голосовании №{self.voting_id}: {voting.title}")
            
            await inter.send(f"Вы проголосовали за {button.label}", ephemeral=True)
            await bot.voting.create_vote(inter.author.id, self.voting_id, type_)

    @disnake.ui.button(label="Согласен", style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        await self.vote(inter, True, button)

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        await self.vote(inter, False, button)

    @disnake.ui.button(label="Окончить голосование", style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(self.voting_id)
        if voting.closed is not None:
            await inter.send("Голосование уже было закрыто", ephemeral=True)
            return

        if inter.permissions.administrator or inter.author.id == voting.author_id:
            await bot.voting.close_voting(self.voting_id)
            logger.info(f"{inter.author.display_name} окончил голосование №{self.voting_id}")
            against, for_ = await bot.voting.get_votes(self.voting_id)
            embed = VotingResultsEmbed(
                bot.get_user(voting.author_id),
                voting.title,
                self.voting_id,
                voting.closed,
                for_,
                against,
                voting.anonym
            )
            await inter.send(embed=embed)
        else:
            await inter.send("У вас нет прав чтобы закрыть петицию", ephemeral=True)

class PetitionView(disnake.ui.View):
    def __init__(self, petition_id: int, timeout: float | None = None) -> None:
        super().__init__(timeout=timeout)
        self.petition_id = petition_id

    @disnake.ui.button(label="Подписать", style=disnake.ButtonStyle.blurple)
    async def sign(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        user = inter.author
        bot: Bot = inter.bot
        sign = await bot.voting.get_sign(inter.author.id, self.petition_id)
        petition = await bot.voting.get_petition(self.petition_id)

        if petition.closed is not None:
            await inter.send(f"Петиция закрыта", ephemeral=True)
            return

        if sign is not None:
            await inter.send(f"Вы уже подписывали петицию", ephemeral=True)
        else:
            logger.info(f"{user.display_name} подписал петицию №{self.petition_id}: {petition.title}")
            
            await inter.send(f"Вы подписали петицию", ephemeral=True)
            await bot.voting.create_sign(inter.author.id, self.petition_id)

    @disnake.ui.button(label="Окончить петицию", style=disnake.ButtonStyle.grey)
    async def stop_petition(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        bot: Bot = inter.bot
        petition = await bot.voting.get_petition(self.petition_id)
        if petition.closed is not None:
            await inter.send("Петиция уже была закрыта", ephemeral=True)
            return

        if inter.permissions.administrator or inter.author.id == petition.author_id:
            await bot.voting.close_petition(self.petition_id)
            logger.info(f"{inter.author.display_name} окончил петицию №{self.petition_id}")
            signs_count = await bot.voting.get_signs(self.petition_id)
            embed = PetitionResultsEmbed(
                bot.get_user(petition.author_id),
                petition.title,
                self.petition_id,
                petition.closed,
                signs_count,
                petition.anonym
            )
            await inter.send(embed=embed)
        else:
            await inter.send("У вас нет прав чтобы закрыть петицию", ephemeral=True)

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
        bot: Bot = self.old_inter.bot
        voting = await bot.voting.get_voting(self.voting_id)
        votes = await bot.voting.get_votes_list(self.voting_id, (self.index - 1) * 20)
        await self.disable_buttons(len(votes))

        if voting.anonym and not self.old_inter.permissions.administrator:
            await self.old_inter.edit_original_response("Данное голосование является аннонимным", view=None)
            return

        if len(votes) == 0:
            await self.old_inter.edit_original_response("Данное голосование пока что не имеет голосов", view=None)
            return

        embed = VotesListEmbed(
            self.old_inter.bot,
            voting,
            votes,
            self.voting_id,
            voting.anonym
        )
        return embed
    
class LineSignsView(AbsList):
    def __init__(self, inter: disnake.MessageInteraction, petition_id: int, index: int = 1) -> None:
        self.petition_id = petition_id
        super().__init__(inter, index, timeout=None)

    async def change(self, offset: int) -> SignsListEmbed | None:
        await super().change(offset)
        bot: Bot = self.old_inter.bot
        petition = await bot.voting.get_petition(self.petition_id)
        signs = await bot.voting.get_signs_list(self.petition_id, (self.index - 1) * 20)
        await self.disable_buttons(len(signs))

        if petition.anonym and not self.old_inter.permissions.administrator:
            await self.old_inter.edit_original_response("Данная петиция является аннонимным", view=None)
            return

        if len(signs) == 0:
            await self.old_inter.edit_original_response("Данная петиция пока что не имеет подписей", view=None)
            return

        embed = SignsListEmbed(
            bot,
            signs,
            self.petition_id,
            petition.anonym
        )
        return embed
    
class LineVotingsView(AbsList):
    async def change(self, offset: int) -> VotingsListEmbed | None:
        await super().change(offset)
        bot: Bot = self.old_inter.bot
        votings = await bot.voting.get_votings_list((self.index - 1) * 20)
        await self.disable_buttons(len(votings))

        if len(votings) == 0:
            await self.old_inter.edit_original_response("Пока что нет голосований", view=None)
            return
        
        embed = VotingsListEmbed(
            bot,
            votings
        )
        return embed
    
class LinePetitionsView(AbsList):
    async def change(self, offset: int) -> PetitionsListEmbed | None:
        await super().change(offset)
        bot: Bot = self.old_inter.bot
        petitions = await bot.voting.get_petitions_list((self.index - 1) * 20)
        await self.disable_buttons(len(petitions))

        if len(petitions) == 0:
            await self.old_inter.edit_original_response("Пока что нет петиций", view=None)
            return
        
        embed = PetitionsListEmbed(
            bot,
            petitions
        )
        return embed
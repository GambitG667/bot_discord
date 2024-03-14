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

    @disnake.ui.button(label="Согласен", style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(self.voting_id)
        await bot.vote(inter, voting, True, button.label)

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(self.voting_id)
        await bot.vote(inter, voting, False, button.label)

    @disnake.ui.button(label="Окончить голосование", style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(self.voting_id)
        await bot.stop_voting(inter, voting, True)

class PetitionView(disnake.ui.View):
    def __init__(self, petition_id: int, timeout: float | None = None) -> None:
        super().__init__(timeout=timeout)
        self.petition_id = petition_id

    @disnake.ui.button(label="Подписать", style=disnake.ButtonStyle.blurple)
    async def sign(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        bot: Bot = inter.bot
        petition = await bot.voting.get_petition(self.petition_id)
        await bot.sign(inter, petition)

    @disnake.ui.button(label="Окончить петицию", style=disnake.ButtonStyle.grey)
    async def stop_petition(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        bot: Bot = inter.bot
        petition = await bot.voting.get_petition(self.petition_id)
        await bot.stop_petition(inter, petition, True)

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

class ActivesListView(AbsList):
    def __init__(self, inter: disnake.MessageInteraction, activity: VotingMaker.Voting | VotingMaker.Petition, index: int = 1) -> None:
        self.no_actives_resp = "Данная петиция пока что не имеет подписей"
        self.anonym_resp = "Данная петиция является аннонимной"
        if isinstance(activity, VotingMaker.Voting):
            self.no_actives_resp = "Данное голосование пока что не имеет голосов"
            self.anonym_resp = "Данное голосование является аннонимным"
        self.activity = activity
        super().__init__(inter, index, timeout=None)

    async def change(self, offset: int) -> ActivesListEmbed | None:
        await super().change(offset)
        bot: Bot = self.old_inter.bot
        if isinstance(self.activity, VotingMaker.Voting):
            activity = await bot.voting.get_voting(self.activity.id)
            actives = await bot.voting.get_votes_list(self.activity.id, (self.index - 1) * 20)
        else:
            activity = await bot.voting.get_petition(self.activity.id)
            actives = await bot.voting.get_signs_list(self.activity.id, (self.index - 1) * 20)
        await self.disable_buttons(len(actives))

        if activity.anonym and not self.old_inter.permissions.administrator:
            await self.old_inter.send(self.no_actives_resp, ephemeral=True)
            return

        if len(actives) == 0:
            await self.old_inter.send(self.anonym_resp, ephemeral=True)
            return

        embed = ActivesListEmbed(
            bot,
            activity,
            actives,
        )
        return embed
    
class ActivitiesListView(AbsList):
    def __init__(self, inter: disnake.MessageInteraction, activities_type: type[VotingMaker.Voting | VotingMaker.Petition], index: int = 1) -> None:
        super().__init__(inter, index, timeout=None)
        self.no_activities_resp = "Пока что нет петиций"
        if activities_type == VotingMaker.Voting:
            self.no_activities_resp = "Пока что нет голосований"
        self.activities_type = activities_type

    async def change(self, offset: int) -> ActivitiesListEmbed | None:
        await super().change(offset)
        bot: Bot = self.old_inter.bot
        if self.activities_type == VotingMaker.Voting:
            activities = await bot.voting.get_votings_list((self.index - 1) * 20)
        else:
            activities = await bot.voting.get_petitions_list((self.index - 1) * 20)
        await self.disable_buttons(len(activities))

        if len(activities) == 0:
            await self.old_inter.send(self.no_activities_resp, ephemeral=True)
            return
        
        embed = ActivitiesListEmbed(
            bot,
            activities
        )
        return embed
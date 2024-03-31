from __future__ import annotations
import disnake
from disnake.ext import commands
from datetime import datetime, timedelta

from views import *
from modals import *
from embeds import *

import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Bot

_voting_id = commands.Param(name="номер_голосования", description="Индивидуальный номер голосования", ge=1)
_voting_anonym = commands.Param(name="анонимное", description="Если голосование аннонимное, то невозможно будет узнать имена проголосовавших", choices=["да", "нет"], default="нет")
_vote_types = commands.Param(name="тип_голоса", description="Тип голоса который вы хотите оставить", choices={"согласен": "Согласен", "не согласен": "Не согласен"})

_petition_id = commands.Param(name="номер_петиции", description="Индивидуальный номер петиции", ge=1)
_petition_anonym = commands.Param(name="анонимная", description="Если петиция аннонимная, то невозможно будет узнать имена подписавших", choices=["да", "нет"], default="нет")

_activity_filter = commands.Param(name="активности", description="Фильтр активностей", choices=["голосования", "петиции", "все"], default="все")
_actives_filter = commands.Param(name="активы", description="Фильтр активов", choices=["голоса", "подписи", "все"], default="все")

_seconds = commands.Param(name="секунды", description="Через сколько секунд активность закроется (могут быть опоздания)", ge=0, lt=60, default=0)
_minute = commands.Param(name="минуты", description="Через сколько минут активность закроется", ge=0, lt=60, default=0)
_hour = commands.Param(name="часы", description="Через сколько часов активность закроется", ge=0, lt=24, default=0)
_day = commands.Param(name="дни", description="Через сколько дней активность закроется", ge=0, lt=365, default=0)

async def check_voting(inter: disnake.CommandInter, id_: int) -> bool:
    bot: Bot = inter.bot
    voting = await bot.voting.get_voting(id_)
    if voting is not None:
        return True
    
async def check_petition(inter: disnake.CommandInter, id_: int) -> bool:
    bot: Bot = inter.bot
    petition = await bot.voting.get_petition(id_)
    if petition is not None:
        return True

class Commons(commands.Cog):
    def __init__(self) -> None:
        for command in self.get_slash_commands():
            command.body.dm_permission = False
            logger.debug(f"В коге {self.qualified_name} зарегестрирована комманда {command.name}")

    @commands.slash_command(
            name="голосование"
    )
    async def voting(inter: disnake.CommandInter, *args) -> None:
        pass

    @voting.sub_command(
            name="создать",
            description="Создать голосование"
    )
    async def create(inter: disnake.CommandInter, anonym: str = _voting_anonym, days: int = _day, hours: int = _hour, minutes: int = _minute, seconds: int = _seconds) -> None:
        b: bool = None
        match anonym:
            case "да":
                b = True
            case "нет":
                b = False
        td = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        await inter.response.send_modal(modal=CreateVotingModal(b, inter.channel.id, td))

    @voting.sub_command(
            name="отобразить",
            description="Отображает голосование по его id"
    )
    async def show(inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(id_)
        if voting is None:
            await inter.send(f"Голосование №{id_} не найдено", ephemeral=True)
            return
        embed = ActivityEmbed(
                await inter.bot.fetch_user(voting.author_id),
                voting
        )
        await inter.send(embed=embed, view=VotingView(id_), ephemeral=True)

    @voting.sub_command(
        name="результаты",
        description="Отображает результаты голосования"
    )
    async def results(inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(id_)
        if voting is None:
            await inter.send(f"Голосование №{id_} не найдено", ephemeral=True)
            return
        count = await bot.voting.get_votes(id_)
        time = voting.closed if voting.closed else datetime.today()
        embed = ResultsEmbed(
            await bot.fetch_user(voting.author_id),
            voting,
            count
        )
        await inter.send(embed=embed, ephemeral=True)
            
    @voting.sub_command(
        name="история",
        description="Отображает список всех голосов в голосовании"
    )
    async def history(inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(id_)
        if voting is None:
            await inter.send(f"Голосование №{id_} не найдено", ephemeral=True)
            return
        view = ActivesListView(inter, voting)
        embed = await view.change(0)
        if embed is not None:
            await inter.send(content=None, view=view, embed=embed, ephemeral=True)

    @voting.sub_command(
        name="список",
        description="Отображает список голосований"
    )
    async def list(inter: disnake.CommandInter) -> None:
        view = ActivitiesListView(inter, VotingMaker.Voting)
        embed = await view.change(0)
        if embed is not None:
            await inter.send(content=None, view=view, embed=embed, ephemeral=True)

    @voting.sub_command(
        name="окончить",
        description="Завершает голосование"
    )
    async def stop_(inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(id_)
        if voting is None:
            await inter.send(f"Голосование №{id_} не найдено", ephemeral=True)
            return
        await bot.stop_voting(inter, voting, False)

    @voting.sub_command(
            name="проголосовать",
            description="Позволяет проголосовать по номеру голосования"
    )
    async def vote(inter: disnake.CommandInter, id_: int = _voting_id, type_: str = _vote_types) -> None:
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(id_)
        if voting is None:
            await inter.send(f"Голосование №{id_} не найдено", ephemeral=True)
            return

        bool_type: bool = None
        match type_:
            case "Согласен":
                bool_type = True
            case "Не согласен":
                bool_type = False
        await bot.vote(inter, voting, bool_type, type_)

    @commands.slash_command(
            name="петиция"
    )
    async def petition(inter: disnake.CommandInter, *args) -> None:
        pass

    @petition.sub_command(
        name="создать",
        description="Создать петицию"
    )
    async def create(inter: disnake.CommandInter, anonym: str = _petition_anonym, days: int = _day, hours: int = _hour, minutes: int = _minute, seconds: int = _seconds) -> None:
        b: bool = None
        match anonym:
            case "да":
                b = True
            case "нет":
                b = False
        td = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        await inter.response.send_modal(CreatePetitionModal(b, inter.channel.id, td))

    @petition.sub_command(
        name="отобразить",
        description="Отображает петицию по его id"
    )
    async def show(inter: disnake.CommandInter, id_: int = _petition_id) -> None:
        bot: Bot = inter.bot
        petition = await bot.voting.get_petition(id_)
        if petition is None:
            await inter.send(f"Петиция №{id_} не найдена", ephemeral=True)
            return
        embed = ActivityEmbed(
                await inter.bot.fetch_user(petition.author_id),
                petition
        )
        await inter.send(embed=embed, view=PetitionView(id_), ephemeral=True)
        

    @petition.sub_command(
        name="результаты",
        description="Отображает результаты петиции"
    )
    async def results(inter: disnake.CommandInter, id_: int = _petition_id) -> None:
        bot: Bot = inter.bot
        petition = await bot.voting.get_petition(id_)
        if petition is None:
            await inter.send(f"Петиция №{id_} не найдена", ephemeral=True)
            return
        count = await bot.voting.get_signs(id_)
        embed = ResultsEmbed(
            await bot.fetch_user(petition.author_id),
            petition,
            count
        )
        await inter.send(embed=embed, ephemeral=True)

    @petition.sub_command(
        name="история",
        description="Отображает список всех подписей в петиции"
    )
    async def history(inter: disnake.CommandInter, id_: int = _petition_id) -> None:
        bot: Bot = inter.bot
        petition = bot.voting.get_petition(id_)
        if petition is None:
            await inter.send(f"Петиция №{id_} не найдена", ephemeral=True)
            return
        view = ActivesListView(inter, petition)
        embed = await view.change(0)
        if embed is not None:
            await inter.send(content=None, view=view, embed=embed, ephemeral=True)

    @petition.sub_command(
        name="список",
        description="Отображает список петиций"
    )
    async def list(inter: disnake.CommandInter) -> None:
        view = ActivitiesListView(inter, VotingMaker.Petition)
        embed = await view.change(0)
        if embed is not None:
            await inter.send(content=None, view=view, embed=embed, ephemeral=True)

    @petition.sub_command(
        name="окончить",
        description="Завершает петицию"
    )
    async def stop_(inter: disnake.CommandInter, id_: int = _petition_id):
        bot: Bot = inter.bot
        petition = await bot.voting.get_petition(id_)
        if petition is None:
            await inter.send(f"Петиция №{id_} не найдена", ephemeral=True)
            return
        await bot.stop_petition(inter, petition, False)

    @petition.sub_command(
        name="подписать",
        description="Позволяет подписывать петиции по их номеру"
    )
    async def sign(inter: disnake.CommandInter, id_: int = _petition_id):
        bot: Bot = inter.bot
        petition = await bot.voting.get_petition(id_)
        if petition is None:
            await inter.send(f"Петиция №{id_} не найдена", ephemeral=True)
            return
        await bot.sign(inter, petition)

    @commands.slash_command(
        name="пользователи"
    )
    async def users(inter: disnake.CommandInter, *args) -> None:
        pass

    @users.sub_command(
        name="история",
        description="Показывает историю подписей и голосов пользователя"
    )
    async def history(inter: disnake.CommandInter, user: disnake.Member, filter = _actives_filter) -> None:
        bot: Bot = inter.bot
        view = ActivesListView(inter, filter, user=user)
        embed = await view.change(0)
        if embed is not None:
            await inter.send(content=None, view=view, embed=embed, ephemeral=True)

    @users.sub_command(
        name="созданные",
        description="Показывает список голосований и петиций, созданные этим пользователем"
    )
    async def created(inter: disnake.CommandInter, user: disnake.Member, filter = _activity_filter) -> None:
        bot: Bot = inter.bot
        view = ActivitiesListView(inter, filter, user=user)
        embed = await view.change(0)
        if embed is not None:
            await inter.send(content=None, view=view, embed=embed, ephemeral=True)
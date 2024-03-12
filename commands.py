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
    from main import Bot

_voting_id = commands.Param(name="id_голосования", description="Индивидуальный номер голосования", ge=1)
_voting_anonym = commands.Param(name="анонимное", description="Если голосование аннонимное, то невозможно будет узнать имена проголосовавших", choices=["да", "нет"], default="да")
_vote_types = commands.Param(name="тип_голоса", description="Тип голоса который вы хотите оставить", choices={"согласен": "Согласен", "не согласен": "Не согласен"})

_petition_id = commands.Param(name="id_петиции", description="Индивидуальный номер петиции", ge=1)
_petition_anonym = commands.Param(name="анонимная", description="Если петиция аннонимная, то невозможно будет узнать имена подписавших", choices=["да", "нет"], default="да")

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
            logger.debug(f"В коге {self.qualified_name} зарегестрирована комманда {command.name}")

    @commands.slash_command(
            name="голосование",
            dm_permition=False
    )
    async def voting(inter: disnake.CommandInter, *args) -> None:
        pass

    @voting.sub_command(
            name="создать",
            description="Создать голосование"
    )
    async def create(inter: disnake.CommandInter, anonym: str = _voting_anonym) -> None:
        b: bool = None
        match anonym:
            case "да":
                b = True
            case "нет":
                b = False
        await inter.response.send_modal(modal=CreateVotingModal(b))

    @voting.sub_command(
            name="отобразить",
            description="Отображает голосование по его id"
    )
    async def show(inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_voting(inter, id_):
            bot: Bot = inter.bot
            voting = await bot.voting.get_voting(id_)
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
            await inter.edit_original_response(f"Голосование №{id_} не найдено")

    @voting.sub_command(
        name="результаты",
        description="Отображает результаты голосования"
    )
    async def results(inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_voting(inter, id_):
            bot: Bot = inter.bot
            voting = await bot.voting.get_voting(id_)
            against, for_ = await bot.voting.get_votes(id_)
            time = voting.closed if voting.closed else datetime.today()
            embed = VotingResultsEmbed(
                bot.get_user(voting.author_id),
                voting.title,
                id_,
                time,
                for_,
                against,
                voting.anonym
            )
            await inter.edit_original_response(embed=embed)
        else:
            await inter.edit_original_response(f"Голосование №{id_} не найдено")

    @voting.sub_command(
        name="история",
        description="Отображает список всех голосов в голосовании"
    )
    async def history(inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_voting(inter, id_):
            view = LineVotesView(inter, id_)
            embed = await view.change(0)
            if embed is not None:
                await inter.edit_original_response(content=None, view=view, embed=embed)
        else:
            await inter.edit_original_response(f"Голосование №{id_} не найдено")

    @voting.sub_command(
        name="список",
        description="Отображает список голосований"
    )
    async def list(inter: disnake.CommandInter) -> None:
        await inter.response.defer(ephemeral=True)
        view = LineVotingsView(inter)
        embed = await view.change(0)
        if embed is not None:
            await inter.edit_original_response(content=None, view=view, embed=embed)

    @voting.sub_command(
        name="окончить",
        description="Завершает голосование"
    )
    async def stop_(inter: disnake.CommandInter, id_: int = _voting_id) -> None:
        await inter.response.defer(ephemeral=True)
        bot: Bot = inter.bot
        voting = await bot.voting.get_voting(id_)
        if voting.closed is not None:
            await inter.edit_original_response("Голосование уже было закрыто")
            return

        if inter.permissions.administrator or inter.author.id == voting.author_id:
            await bot.voting.close_voting(id_)
            logger.info(f"{inter.author.display_name} окончил голосование №{id_}")
        else:
            await inter.edit_original_response("У вас нет прав чтобы закрыть петицию")

    @voting.sub_command(
            name="проголосовать",
            description="Позволяет проголосовать по номеру голосования"
    )
    async def vote(inter: disnake.CommandInter, id_: int = _voting_id, type_: str = _vote_types) -> None:
        await inter.response.defer(ephemeral=True)
        user = inter.author
        bot: Bot = inter.bot
        vote = await bot.voting.get_vote(inter.author.id, id_)
        voting = await bot.voting.get_voting(id_)

        bool_type: bool = None
        match type_:
            case "Согласен":
                bool_type = True
            case "Не согласен":
                bool_type = False
        t: bool | None = None
        if vote is not None:
            t = vote.type

        if voting.closed is not None:
            await inter.edit_original_response(f"Голосование закрыто")
            return

        if t == bool_type:
            await inter.edit_original_response(f"Вы уже проголосовали за {type_}")
        else:
            logger.info(f"{user.display_name} прологосовал за \"{type_}\" в голосовании №{id_}: {voting.title}")
            
            await inter.edit_original_response(f"Вы проголосовали за {type_}")
            await bot.voting.create_vote(inter.author.id, id_, bool_type)

    @commands.slash_command(
            name="петиция",
            dm_permission=False
    )
    async def petition(inter: disnake.CommandInter, *args) -> None:
        pass

    @petition.sub_command(
        name="создать",
        description="Создать петицию"
    )
    async def create(inter: disnake.CommandInter, anonym: str = _petition_anonym) -> None:
        b: bool = None
        match anonym:
            case "да":
                b = True
            case "нет":
                b = False
        await inter.response.send_modal(CreatePetitionModal(b))

    @petition.sub_command(
        name="отобразить",
        description="Отображает петицию по его id"
    )
    async def show(inter: disnake.CommandInter, id_: int = _petition_id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_petition(inter, id_):
            bot: Bot = inter.bot
            petition = await bot.voting.get_petition(id_)
            embed = PetitionEmbed(
                    inter.bot.get_user(petition.author_id),
                    petition.title,
                    petition.description,
                    id_,
                    petition.created,
                    petition.anonym
            )
            await inter.edit_original_response(embed=embed, view=PetitionView(id_))
        else:
            await inter.edit_original_response(f"Петиция №{id_} не найдена")

    @petition.sub_command(
        name="результаты",
        description="Отображает результаты петиции"
    )
    async def results(inter: disnake.CommandInter, id_: int = _petition_id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_petition(inter, id_):
            bot: Bot = inter.bot
            petition = await bot.voting.get_petition(id_)
            signs_count = await bot.voting.get_signs(id_)
            time = petition.closed if petition.closed else datetime.today()
            embed = PetitionResultsEmbed(
                bot.get_user(petition.author_id),
                petition.title,
                id_,
                time,
                signs_count,
                petition.anonym
            )
            await inter.edit_original_response(embed=embed)
        else:
            await inter.edit_original_response(f"Петиция №{id_} не найдено")

    @petition.sub_command(
        name="история",
        description="Отображает список всех подписей в петиции"
    )
    async def history(inter: disnake.CommandInter, id_: int = _petition_id) -> None:
        await inter.response.defer(ephemeral=True)
        if await check_petition(inter, id_):
            view = LineSignsView(inter, id_)
            embed = await view.change(0)
            if embed is not None:
                await inter.edit_original_response(content=None, view=view, embed=embed)
        else:
            await inter.edit_original_response(f"Голосование №{id_} не найдено")

    @petition.sub_command(
        name="список",
        description="Отображает список петиций"
    )
    async def list(inter: disnake.CommandInter) -> None:
        await inter.response.defer(ephemeral=True)
        view = LinePetitionsView(inter)
        embed = await view.change(0)
        if embed is not None:
            await inter.edit_original_response(content=None, view=view, embed=embed)

    @petition.sub_command(
        name="окончить",
        description="Завершает петицию"
    )
    async def stop_(inter: disnake.CommandInter, id_: int = _petition_id):
        await inter.response.defer(ephemeral=True)
        bot: Bot = inter.bot
        petition = await bot.voting.get_petition(id_)
        if petition.closed is not None:
            await inter.edit_original_response("Петиция уже была закрыта")
            return

        if inter.permissions.administrator or inter.author.id == petition.author_id:
            await bot.voting.close_petition(id_)
            logger.info(f"{inter.author.display_name} окончил петицию №{id_}")
        else:
            await inter.edit_original_response("У вас нет прав чтобы закрыть петицию")

    @petition.sub_command(
        name="подписать",
        description="Позволяет подписывать петиции по их номеру"
    )
    async def sign(inter: disnake.CommandInter, id_: int = _petition_id):
        await inter.response.defer(ephemeral=True)
        user = inter.author
        bot: Bot = inter.bot
        sign = await bot.voting.get_sign(inter.author.id, id_)
        petition = await bot.voting.get_petition(id_)

        if petition.closed is not None:
            await inter.edit_original_response(f"Петиция закрыта")
            return

        if sign is not None:
            await inter.edit_original_response(f"Вы уже подписывали петицию")
        else:
            logger.info(f"{user.display_name} подписал петицию №{id_}: {petition.title}")
            
            await inter.edit_original_response(f"Вы подписали петицию")
            await bot.voting.create_sign(inter.author.id, id_)
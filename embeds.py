from __future__ import annotations
import disnake
from disnake.ext import commands
from datetime import datetime
from voting import VotingMaker
import traceback

import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Bot
    from commands import Commons

def anonym(bool: bool) -> str:
    text = ""
    if bool:
        text = "(Анонимно)"
    return text

class ActivityEmbed(disnake.Embed):
    def __init__(self, inter: disnake.Interaction, author: disnake.Member | disnake.User, activity: VotingMaker.Voting | VotingMaker.Petition) -> None:
        anon = anonym(activity.anonym)
        bot: Bot = inter.bot

        t = "\n\n> Если кнопки перестали работать, используйте команды [*/{}*] для голосования и [*/{}*] для завершения"
        coms: Commons = bot.get_cog("Commons")
        if isinstance(activity, VotingMaker.Voting):
            f = (coms.vote.qualified_name, coms.stop_voting.qualified_name)
        elif isinstance(activity, VotingMaker.Petition):
            f = (coms.sign.qualified_name, coms.stop_petition.qualified_name)

        desc = activity.description + t.format(*f)

        super().__init__(title=activity.title, description=desc, timestamp=activity.created, color=disnake.Colour.red())
        self.set_author(name=author.display_name, icon_url=author.display_avatar.url)
        self.set_footer(text=f"{str(activity).capitalize()} №{activity.id} {anon}")

class ResultsEmbed(disnake.Embed):
    def __init__(self, author: disnake.User, activity: VotingMaker.Voting | VotingMaker.Petition, count: VotingMaker.VotesCount | VotingMaker.SignsCount) -> None:
        anon = anonym(activity.anonym)

        super().__init__(title=activity.title, description=activity.description, timestamp=activity.created, color=disnake.Colour.red())
        if isinstance(activity, VotingMaker.Voting):
            self.add_field("Согласны", count.to, inline=True)
            self.add_field("Не согласны", count.against, inline=True)
        else:
            self.add_field("Подписи", count.count, inline=False)
        self.set_author(name=author.display_name, icon_url=author.display_avatar.url)
        self.set_footer(text=f"{str(activity).capitalize()} №{activity.id} {anon}")  

class ActivesListEmbed(disnake.Embed):
    def __init__(self, bot: Bot, activity: VotingMaker.Voting | VotingMaker.Petition | None, actives_list: list[VotingMaker.Vote | VotingMaker.Sign], start: int, user: disnake.Member | None = None) -> None:
        if user is None:
            anon = anonym(activity.anonym)

            super().__init__(title=activity.title, description=activity.description, timestamp=activity.created, color=disnake.Colour.red())
            self.set_footer(text=f"{str(activity).capitalize()}№{activity.id} {anon}")
            user = bot.get_user(activity.author_id)
        else:
            super().__init__(color=disnake.Colour.red())
            self.set_footer(text=bot.user.display_name)

        for i, a in enumerate(actives_list):
            if i == 20:
                break
            if isinstance(a, VotingMaker.Vote):
                t = ": Не согласен"
                if a.type:
                    t = ": Согласен"
                id_ = a.voting_id
            else:
                t = ""
                id_ = a.petition_id
            self.add_field(f"{start + i + 1}. {str(a).capitalize()} №*{id_}* - **{bot.get_user(a.user_id).display_name}**{t}", f"<t:{int(a.created.timestamp())}>", inline=False)
        self.set_author(name=user.display_name, icon_url=user.display_avatar.url)

class ActivitiesListEmbed(disnake.Embed):
    def __init__(self, bot: Bot, activitiesList: list[VotingMaker.Voting | VotingMaker.Petition], start: int, user: disnake.Member | None = None) -> None:
        types_set = set(map(type, activitiesList))
        title = ["Список"]
        if len(types_set) == 1 and user is None:
            a = types_set.pop()
            title.append(a.__str__(None)[:-1] + "й")
        super().__init__(title=" ".join(title), color=disnake.Colour.red())
        for i, a in enumerate(activitiesList):
            if i == 20:
                break

            t = [f"Открыто: <t:{int(a.created.timestamp())}>."]
            if a.closed is not None:
                t.append(f"Закрыто: <t:{int(a.closed.timestamp())}>.")
            
            t.append(anonym(a.anonym))
            self.add_field(f"{start + i + 1}. *{str(a).capitalize()} №{a.id}* - {bot.get_user(a.author_id).display_name}: **{a.title}**", " ".join(t), inline=False)
        if user is not None:
            self.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        self.set_footer(text=bot.user.display_name)

class ErrorEmbed(disnake.Embed):
    """Используется с вебхуками"""
    def __init__(self, inter: disnake.CommandInter, bot: Bot, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        s = str(error)
        if len(s) > 256:
            s = s[:253] + "..."
        super().__init__(title=f"{s}", description=f"```{''.join(traceback.format_exception(error))}```", color=disnake.Colour.red())
        self.set_author(name=inter.author.display_name, icon_url=inter.author.display_avatar.url)
        self.set_footer(text=f"[{inter.application_command.qualified_name}]")
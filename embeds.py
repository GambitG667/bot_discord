from __future__ import annotations
import disnake
from disnake.ext import commands
from datetime import datetime
from voting import VotingMaker

import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Bot

def anonym(bool: bool) -> str:
    text = ""
    if bool:
        text = "(Анонимно)"
    return text

def get_footer(activity: VotingMaker.Voting | VotingMaker.Petition):
    if isinstance(activity, VotingMaker.Voting):
        return "Голосование"
    else:
        return "Петиция"

class ActivityEmbed(disnake.Embed):
    def __init__(self, author: disnake.User, activity: VotingMaker.Voting | VotingMaker.Petition) -> None:
        anon = anonym(activity.anonym)

        super().__init__(title=activity.title, description=activity.description, timestamp=activity.created, color=disnake.Colour.red())
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"{get_footer(activity)} №{activity.id} {anon}")

class ResultsEmbed(disnake.Embed):
    def __init__(self, author: disnake.User, activity: VotingMaker.Voting | VotingMaker.Petition, count: VotingMaker.VotesCount | VotingMaker.SignsCount) -> None:
        anon = anonym(activity.anonym)

        super().__init__(title=activity.title, description=activity.description, timestamp=activity.created, color=disnake.Colour.red())
        if isinstance(activity, VotingMaker.Voting):
            self.add_field("Согласны", count.to, inline=True)
            self.add_field("Не согласны", count.against, inline=True)
        else:
            self.add_field("Подписи", count.count, inline=False)
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"{get_footer(activity)} №{activity.id} {anon}")  

class ActivesListEmbed(disnake.Embed):
    def __init__(self, bot: Bot, activity: VotingMaker.Voting | VotingMaker.Petition, actives_list: list[VotingMaker.VoteWithIndex | VotingMaker.SignWithIndex]) -> None:
        anon = anonym(activity.anonym)

        super().__init__(title=activity.title, description=activity.description, timestamp=activity.created, color=disnake.Colour.red())
        for i, a in enumerate(actives_list):
            if i == 20:
                break
            if isinstance(a, VotingMaker.VoteWithIndex):
                t = "Не согласен"
                if a.vote.type:
                    t = "Согласен"
                self.add_field(f"Голос №*{a.index}*. **{bot.get_user(a.vote.user_id).display_name}**: {t}", f"<t:{int(a.vote.created.timestamp())}>", inline=False)
                
            else:
                self.add_field(f"Подпись №*{a.index}*. **{bot.get_user(a.sign.user_id).display_name}**", f"<t:{int(a.sign.created.timestamp())}>", inline=False)
        author = bot.get_user(activity.author_id)
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"{get_footer(activity)}№{activity.id} {anon}")

class ActivitiesListEmbed(disnake.Embed):
    def __init__(self, bot: commands.InteractionBot, activitiesList: list[VotingMaker.Voting | VotingMaker.Petition]) -> None:
        types_set = set(map(type, activitiesList))
        title = ["Список"]
        if len(types_set) == 1:
            a = types_set.pop()
            if isinstance(a, VotingMaker.Voting):
                title.append("голосований")
            else:
                title.append("петиций")
        super().__init__(title=" ".join(title), color=disnake.Colour.red())
        for i, a in enumerate(activitiesList):
            if i == 20:
                break

            t = [f"Открыто: <t:{int(a.created.timestamp())}>."]
            if a.closed is not None:
                t.append(f"Закрыто: <t:{int(a.closed.timestamp())}>.")
            
            t.append(anonym(a.anonym))
            self.add_field(f"*{get_footer(a)} №{a.id}*. {bot.get_user(a.author_id).display_name}: **{a.title}**", " ".join(t), inline=False)
        self.set_footer(text=bot.user.display_name)
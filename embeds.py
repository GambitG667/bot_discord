from __future__ import annotations
import disnake
from disnake.ext import commands
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from voting import VotingMaker

def anonym(bool: bool) -> str:
    text = ""
    if bool:
        text = "(Анонимно)"
    return text

class AbsEmbed(disnake.Embed):
    def __init__(self, author: disnake.User , title: str, desc: str, id_: int, time: datetime, footer: str, is_anonym: bool = False) -> None:
        is_anonym = anonym(is_anonym)

        super().__init__(title=title, description=desc, timestamp=time, color=disnake.Colour.red())
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"{footer} №{id_} {is_anonym}")

class VotingEmbed(AbsEmbed):
    def __init__(self, author: disnake.User , title: str, desc: str, id_: int, time: datetime, is_anonym: bool = False) -> None:
        super().__init__(author=author, title=title, desc=desc, id_=id_, time=time, footer="Голосование", is_anonym=is_anonym)

class PetitionEmbed(AbsEmbed):
    def __init__(self,  author: disnake.User, title: str, desc: str, id_: int, time: datetime, is_anonym: bool = False) -> None:
        super().__init__(author=author, title=title, desc=desc, id_=id_, time=time, footer="Петиция", is_anonym=is_anonym)

class VotingResultsEmbed(disnake.Embed):
    def __init__(self, author: disnake.User, title: str, id_: int, time: datetime, for_: int, against: int, is_anonym: bool = False) -> None:
        is_anonym = anonym(is_anonym)

        super().__init__(title=title, timestamp=time, color=disnake.Colour.red())
        self.add_field("Согласны", for_, inline=True)
        self.add_field("Не согласны", against, inline=True)
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"Голосование №{id_} {is_anonym}")

class PetitionResultsEmbed(disnake.Embed):
    def __init__(self, author: disnake.User, title: str, id_: int, time: datetime, signs_count: int, is_anonym: bool = False) -> None:
        is_anonym = anonym(is_anonym)

        super().__init__(title=title, timestamp=time, color=disnake.Colour.red())
        self.add_field("Подписи", signs_count, inline=False)
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"Петиция №{id_} {is_anonym}")

class VotesListEmbed(disnake.Embed):
    def __init__(self, bot: commands.InteractionBot, votesList: list[VotingMaker.VoteWithIndex], id_: int, is_anonym: bool = False) -> None:
        is_anonym = anonym(is_anonym)

        super().__init__(title=f"Список голосов", color=disnake.Colour.red())
        for i, v in enumerate(votesList):
            if i == 20:
                break
            t = "Не согласен"
            if v.vote.type:
                t = "Согласен"
            self.add_field(f"*{v.index}*. **{bot.get_user(v.vote.user_id).display_name}**: {t}", f"<t:{int(v.vote.created.timestamp())}>", inline=False)
        self.set_footer(text=f"Голосование №{id_} {is_anonym}")

class SignsListEmbed(disnake.Embed):
    def __init__(self, bot: commands.InteractionBot, signsList: list[VotingMaker.SignWithIndex], id_: int, is_anonym: bool = False) -> None:
        is_anonym = anonym(is_anonym)

        super().__init__(title="Список подписей", color=disnake.Colour.red())
        for i, v in enumerate(signsList):
            if i == 20:
                break

            self.add_field(f"*{v.index}*. **{bot.get_user(v.sign.user_id).display_name}**", f"<t:{int(v.sign.created.timestamp())}>", inline=False)
        self.set_footer(text=f"Петиция №{id_} {is_anonym}")

class VotingsListEmbed(disnake.Embed):
    def __init__(self, bot: commands.InteractionBot, votingsList: list[VotingMaker.Voting]) -> None:
        super().__init__(title="Список голосований", color=disnake.Colour.red())
        for i, v in enumerate(votingsList):
            if i == 20:
                break

            t = [f"Открыто: <t:{int(v.created.timestamp())}>."]
            if v.closed is not None:
                t.append(f"Закрыто: <t:{int(v.closed.timestamp())}>.")
            
            t.append(anonym(v.anonym))
            self.add_field(f"*{v.id}*. {bot.get_user(v.author_id).display_name}: **{v.title}**", " ".join(t), inline=False)
        self.set_footer(text=bot.user.display_name)

class PetitionsListEmbed(disnake.Embed):
    def __init__(self, bot: commands.InteractionBot, petitionsList: list[VotingMaker.Petition]) -> None:
        super().__init__(title="Список петиций", color=disnake.Colour.red())
        for i, p in enumerate(petitionsList):
            if i == 20:
                break

            t = [f"Открыто: <t:{int(p.created.timestamp())}>."]
            if p.closed is not None:
                t.append(f"Закрыто: <t:{int(p.closed.timestamp())}>.")
            
            t.append(anonym(p.anonym))
            self.add_field(f"*{p.id}*. {bot.get_user(p.author_id).display_name}: **{p.title}**", " ".join(t), inline=False)
        self.set_footer(text=bot.user.display_name)
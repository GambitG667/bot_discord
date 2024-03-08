from typing import Any, Optional, Union
import disnake
from disnake.colour import Colour
from disnake.ext import commands
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

def anonym(bool):
    text = ""
    if bool:
        text = " (Анонимно)"
    return text

class VotingEmbed(disnake.Embed):
    def __init__(self, author: disnake.User , title: str, desc: str, id_: int, time: datetime, is_anonym: bool = False):
        is_anonym = anonym(is_anonym)

        super().__init__(title=title, description=desc, timestamp=time, color=disnake.Colour.red())
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"Голосование №{id_}{is_anonym}")

class ResultsEmbed(disnake.Embed):
    def __init__(self, author: disnake.User, title: str, id_: int, time: datetime, for_: int, against: int, is_anonym: bool = False):
        is_anonym = anonym(is_anonym)

        super().__init__(title=title, timestamp=time, color=disnake.Colour.red())
        self.add_field("Согласны", for_, inline=True)
        self.add_field("Не согласны", against, inline=True)
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"Голосование №{id_}{is_anonym}")

class VotesListEmbed(disnake.Embed):
    def __init__(self, bot: commands.InteractionBot, votesList: list, id_: int, is_anonym: bool = False):
        is_anonym = anonym(is_anonym)

        super().__init__(title=f"Список голосов", color=disnake.Colour.red())
        for i, l in enumerate(votesList):
            if i == 20:
                break
            j = l[0]
            vote = l[1]
            t = "Не согласен"
            if vote.type:
                t = "Согласен"
            self.add_field(f"*{j}*: **{bot.get_user(vote.user_id).display_name}**: {t}", f"<t:{int(vote.created.timestamp())}>", inline=False)
        self.set_footer(text=f"Голосование №{id_}{is_anonym}")
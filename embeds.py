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
    def __init__(self, author, title, desc, id_, time, is_anonym=False):
        is_anonym = anonym(is_anonym)

        super().__init__(title=title, description=desc, timestamp=time, color=disnake.Colour.red())
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"Голосование №{id_}{is_anonym}")

class ResultsEmbed(disnake.Embed):
    def __init__(self, author, title, id_, time, for_, against, is_anonym=False):
        is_anonym = anonym(is_anonym)

        super().__init__(title=title, timestamp=time, color=disnake.Colour.red())
        self.add_field("Согласны", for_, inline=True)
        self.add_field("Не согласны", against, inline=True)
        self.set_author(name=f"{author.display_name}", icon_url=author.display_avatar.url)
        self.set_footer(text=f"Голосование №{id_}{is_anonym}")
import disnake
from disnake.ext import commands
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

async def command(inter, title: str, text: str):
    if inter.author.nick:
        author_name = f"{inter.author.nick} ({inter.author.name})"
    else:
        author_name = f"{inter.author.name}"
    embed = disnake.Embed(
            title=title,
            description=text,
            colour=disnake.Colour.red(),
            timestamp=datetime.today(),
    )
    embed.set_author(name=f"{author_name}")
    embed.set_footer(text=f"Голосование №0")
    view = Voting(inter.author.name)

    logger.info(f"{inter.author.name} начал голосование: {title} => {text}")
    await inter.send(embed=embed, view=view)
    message = await inter.original_message()

    inter.bot.db.start_voting(message.id, title, text, inter.author.id)
    view.message_id = message.id

start_voting = commands.InvokableSlashCommand(
    command,
    name="sv",
    description="Начать голосование.",
    dm_permission=False
)

class Voting(disnake.ui.View):
    def __init__(self, author, timeout = None):
        super().__init__(timeout=timeout)
        self.author = author

    @disnake.ui.button(label="Согласен", style=disnake.ButtonStyle.green)
    async def confirm(self, button, inter):
        user = inter.author
        t = inter.bot.db.get_vote_index(inter.author.id, self.message_id, 2)
        if t:
            await inter.send(f"Вы уже проголосовали за {button.label}", ephemeral=True)
        else:
            logger.info(f"{inter.author.name} прологосовал за \"{button.label}\"")

            await inter.send(f"Вы проголосовали за {button.label}", ephemeral=True)
            inter.bot.db.vote(inter.author.id, self.message_id, True)

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cancel(self, button, inter):
        user = inter.author
        t = inter.bot.db.get_vote_index(inter.author.id, self.message_id, 2)
        if not t:
            await inter.send(f"Вы уже проголосовали за {button.label}", ephemeral=True)
        else:
            logger.info(f"{inter.author.name} проголосовал за \"{button.label}\"")

            await inter.send(f"Вы проголосовали за {button.label}", ephemeral=True)
            inter.bot.db.vote(inter.author.id, self.message_id, False)

    @disnake.ui.button(label="Окончить голосование", style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button, inter):
        if inter.permissions.administrator or inter.author.name == self.author:
            if hasattr(self, "message_id"):
                message = inter.bot.get_message(self.message_id)
                await message.delete()
            inter.bot.db.stop_voting(self.message_id)
            logger.info(f"{inter.author.name} окончил голосование")
            await inter.send("Голосование окончено", ephemeral=True)

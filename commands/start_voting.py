import disnake
from disnake.ext import commands
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

async def command(inter):
    await inter.response.send_modal(modal=Modal()) 

start_voting = commands.InvokableSlashCommand(
    command,
    name="голосование",
    description="Начать голосование.",
    dm_permission=False
)

class Modal(disnake.ui.Modal):
    def __init__(self):
        comp = [
            disnake.ui.TextInput(
                label = "Заголовок",
                placeholder = "Напишите тему голосования",
                custom_id = "title",
                style=disnake.TextInputStyle.short,
                max_length=20
            ),
            disnake.ui.TextInput(
                label = "Описание",
                placeholder = "Напишите полное описание голосования",
                custom_id = "description",
                style=disnake.TextInputStyle.paragraph
            )
        ]
        super().__init__(
            title="Голосование",
            custom_id="voting",
            components=comp
        )

    async def callback(self, inter):
        title = inter.text_values["title"]
        text = inter.text_values["description"]
        if inter.author.nick:
            author_name = f"{inter.author.nick} ({inter.author.name})"
        else:
            author_name = f"{inter.author.name}"
        embed = disnake.Embed(
                title=title,
                description=text,
                colour=disnake.Colour.red(),
                timestamp=datetime.today()
        )
        embed.set_author(name=f"{author_name}")
        embed.set_footer(text=f"Голосование №0")
        view = Voting(inter.author.name)

        logger.info(f"{inter.author.name} начал голосование: {title} => {text}")
        await inter.send(embed=embed, view=view)
        message = await inter.original_message()

        await inter.bot.db.start_voting(message.id, title, text, inter.author.id)
        view.message_id = message.id

class Voting(disnake.ui.View):
    def __init__(self, author, timeout = None):
        super().__init__(timeout=timeout)
        self.author = author
        self.message_id = None

    @disnake.ui.button(label="Согласен", style=disnake.ButtonStyle.green)
    async def confirm(self, button, inter):
        user = inter.author
        vote = await inter.bot.db.get_vote(inter.author.id, self.message_id)
        t = None
        if vote is not None:
            t = vote.type
        if t == True:
            await inter.send(f"Вы уже проголосовали за {button.label}", ephemeral=True)
        else:
            logger.info(f"{inter.author.name} прологосовал за \"{button.label}\"")

            await inter.send(f"Вы проголосовали за {button.label}", ephemeral=True)
            await inter.bot.db.vote(inter.author.id, self.message_id, True)

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cancel(self, button, inter):
        user = inter.author
        vote = await inter.bot.db.get_vote(inter.author.id, self.message_id)
        t = None
        if vote is not None:
            t = vote.type
        if t == False:
            await inter.send(f"Вы уже проголосовали за {button.label}", ephemeral=True)
        else:
            logger.info(f"{inter.author.name} проголосовал за \"{button.label}\"")

            await inter.send(f"Вы проголосовали за {button.label}", ephemeral=True)
            await inter.bot.db.vote(inter.author.id, self.message_id, False)

    @disnake.ui.button(label="Окончить голосование", style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button, inter):
        if inter.permissions.administrator or inter.author.name == self.author:
            if hasattr(self, "message_id"):
                message = inter.bot.get_message(self.message_id)
                await message.delete()
            await inter.bot.db.close_voting(self.message_id)
            logger.info(f"{inter.author.name} окончил голосование")
            await inter.send("Голосование окончено", ephemeral=True)

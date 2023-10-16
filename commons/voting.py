import disnake
from disnake.ext import commands
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

@commands.slash_command(
        name="голосование",
        description="Команда для работы с голосованиями",
        dm_permission=False
)
async def voting(inter, *args):
    pass

@voting.sub_command(
        name="создать",
        description="Создать голосование"
)
async def create(inter):
    await inter.response.send_modal(modal=CreateModal())

class CreateModal(disnake.ui.Modal):
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

        voting_id = await inter.bot.db.start_voting(title, text, inter.author.id)

        embed = disnake.Embed(
                title=title,
                description=text,
                colour=disnake.Colour.red(),
                timestamp=datetime.today()
        )
        embed.set_author(name=f"{author_name}")
        embed.set_footer(text=f"Голосование №{voting_id}")
        view = CreateView(inter.author.name, voting_id)

        logger.info(f"{inter.author.name} начал голосование: {title} => {text}")
        await inter.send(embed=embed, view=view)

class CreateView(disnake.ui.View):
    def __init__(self, author, voting_id,  timeout = None):
        super().__init__(timeout=timeout)
        self.author = author
        self.voting_id = voting_id

    async def vote(self, inter, type_, label):
        user = inter.author
        vote = await inter.bot.db.get_vote(inter.author.id, self.voting_id)
        t = None
        if vote is not None:
            t = vote.type
        if t == type_:
            await inter.send(f"Вы уже проголосовали за {label}", ephemeral=True)
        else:
            logger.info(f"{user.name} прологосовал за \"{label}\"")

            await inter.send(f"Вы проголосовали за {label}", ephemeral=True)
            await inter.bot.db.create_vote(inter.author.id, self.voting_id, type_)

    @disnake.ui.button(label="Согласен", style=disnake.ButtonStyle.green)
    async def confirm(self, button, inter):
        await self.vote(inter, True, button.label)

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cancel(self, button, inter):
        await self.vote(inter, False, button.label)

    @disnake.ui.button(label="Окончить голосование", style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button, inter):
        if inter.permissions.administrator or inter.author.name == self.author:
            await inter.bot.db.close_voting(self.voting_id)
            logger.info(f"{inter.author.name} окончил голосование")
            await inter.send("Голосование окончено", ephemeral=True)

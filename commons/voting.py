import disnake
from disnake.ext import commands
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

@commands.slash_command(
        name="голосование",
        description="Команда для работы с голосованиями",
        dm_permition=False
)
async def voting(inter, *args):
    pass

@voting.sub_command(
        name="создать",
        description="Создать голосование"
)
async def create(inter, anonym: bool = False):
    await inter.response.send_modal(modal=CreateModal(anonym))

@voting.sub_command(
        name="отобразить",
        description="Отображает голосование по его id"
)
async def show(inter, id_: str):
    voting = await inter.bot.db.get_voting(id_)
    if voting:
        embed = await voting_embed(
                inter,
                voting.title,
                voting.description,
                id_,
                voting.created,
                voting.anonym
        )
        await inter.send(embed=embed, view=VotingView(id_), ephemeral=True)
    else:
        await inter.send("Голосование {id_} не найден")
    logger.info(f"{inter.author.display_name} отобразил голосование{_id}")

async def voting_embed(inter, title, desc, id_, time, is_anonym=False):
    if is_anonym:
        is_anonym = " (Анонимно)"
    else:
        is_anonym = ""

    embed = disnake.Embed(
        title=title,
        description=desc,
        colour=disnake.Colour.red(),
        timestamp=time
    )
    embed.set_author(name=f"{inter.author.display_name}", icon_url=inter.author.display_avatar.url)
    embed.set_footer(text=f"Голосование №{id_}{is_anonym}")
    return embed

class CreateModal(disnake.ui.Modal):
    def __init__(self, anonym):
        self.anonym = anonym
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
                style=disnake.TextInputStyle.long
            )
        ]
        super().__init__(
            title="Голосование",
            custom_id="voting",
            components=comp
        )

    async def callback(self, inter):
        title = inter.text_values["title"]
        desc = inter.text_values["description"]

        voting_id = await inter.bot.db.start_voting(title, desc, inter.author.id, self.anonym)
        view = VotingView(voting_id)

        embed = await voting_embed(
            inter,
            title,
            desc,
            voting_id,
            datetime.today(),
            self.anonym
        )

        logger.info(f"{inter.author.display_name} начал голосование: {title} => {desc}")
        await inter.send("@everyone", embed=embed, view=view)

class VotingView(disnake.ui.View):
    def __init__(self, voting_id,  timeout = None):
        super().__init__(timeout=timeout)
        self.voting_id = voting_id

    async def vote(self, inter, type_, label):
        user = inter.author
        vote = await inter.bot.db.get_vote(inter.author.id, self.voting_id)
        voting = await inter.bot.db.get_voting(self.voting_id)
        t = None
        if vote is not None:
            t = vote.type

        if voting.closed is not None:
            await inter.send(f"Голосование закрыто", ephemeral=True)
            return

        if t == type_:
            await inter.send(f"Вы уже проголосовали за {label}", ephemeral=True)
        else:
            logger.info(f"{user.display_name} прологосовал за \"{label}\"")

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
        voting = await inter.bot.db.get_voting(self.voting_id)
        if voting.closed is not None:
            await inter.send("Голосование уже было закрыто", ephemeral=True)
            return

        if inter.permissions.administrator or inter.author.id == self.author.id:
            await inter.bot.db.close_voting(self.voting_id)
            logger.info(f"{inter.author.display_name} окончил голосование")
            await inter.send("Голосование окончено", ephemeral=True)

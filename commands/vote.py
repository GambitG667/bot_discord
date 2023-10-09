import disnake
from disnake.ext import commands
from datetime import datetime

async def func(inter, title: str, text: str):
    embed = disnake.Embed(
            title=title,
            description=text,
            colour=disnake.Colour.red(),
            timestamp=datetime.today(),
    )
    embed.set_author(name=f"Голосование №")
    embed.set_footer(text=f"Голосование начал {inter.author.name}")
    view = Voting()
    await inter.send(embed=embed, view=view)
    view.messageId = (await inter.original_message()).id

command = commands.InvokableSlashCommand(
    func,
    name="sv",
    description="Начать голосование.",
    dm_permission=False
)

class Voting(disnake.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.value = dict()

    @disnake.ui.button(label="Согласен", style=disnake.ButtonStyle.green)
    async def confirm(self, button, inter):
        user = inter.author
        if self.value.get(user.name) == True:
            await inter.send(f"Вы уже проголосовали за {button.label}", ephemeral=True)
        else:
            await inter.send(f"Вы прологосовали за {button.label}", ephemeral=True)
            self.value[user.name] = True

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cancel(self, button, inter):
        user = inter.author
        if self.value.get(user.name) == False:
            await inter.send(f"Вы уже проголосовали за {button.label}", ephemeral=True)
        else:
            await inter.send(f"Вы прологосовали за {button.label}", ephemeral=True)
            self.value[user.name] = False

    @disnake.ui.button(label="Окончить голосование", style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button, inter):
        if inter.permissions.administrator:
            if hasattr(self, "messageId"):
                message = inter.bot.get_message(self.messageId)
                await message.delete()
            await inter.send("Голосование окончено", ephemeral=True)
            self.stop()

import disnake
from disnake.ext import commands
from secret import TOKEN


bot = commands.Bot(command_prefix="$",
                   help_command=None,
                   intents=disnake.Intents.all())

@bot.event
async def on_ready():
    print(f"Бот {bot.user} готов!")

@bot.slash_command(name="ping-pong",description="just game")
async def ping(inter):
    await inter.response.send_message("понг")

@bot.command(name="привет")
async def hello(inter):
    await inter.send("привет")

@bot.command(name="voting")
async def voting(ctx, *,reason = ""):
    view = Voting()
    print(f"{ctx.author} начинает голосование {reason}")
    await ctx.send(f"Голосуем {reason}", view=view)
    await view.wait()
    cansel = 0
    confirm = 0
    for key in view.value.keys():
        if view.value[key]:
            confirm +=1
        else:
            cansel += 1
    print(f"голосование окончено\nза - {confirm}\nпротив - {cansel}")
    await ctx.send(f"Голосование окончено\nза - {confirm}\nпротив - {cansel}")

class Voting(disnake.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.value = dict()
    
    @disnake.ui.button(label="Согласен", style=disnake.ButtonStyle.green)
    async def confirm(self, button, inter):
        self.value[inter.author.name] = True
        await inter.response.send_message('Вы проголосовали за', ephemeral=True)
        print(f"{inter.author} проголосовал за")

    @disnake.ui.button(label="Не согласен", style=disnake.ButtonStyle.red)
    async def cansel(self, button, inter):
        self.value[inter.author.name] = False
        await inter.response.send_message('Вы проголосовали против', ephemeral=True)
        print(f"{inter.author} проголосовал против")
    
    @disnake.ui.button(label="остановить голосование",style=disnake.ButtonStyle.grey)
    async def stop_voting(self, button, inter):
        if inter.permissions.administrator:
            await inter.response.send_message('Голосование остановлено', ephemeral=True)
            print(f"{inter.author} останавливает голосование")
            self.stop()
        else:
            await inter.response.send_message("У вас недостаточно прав для этого", ephemeral=True)


bot.run(TOKEN)
import disnake
from disnake.ext import commands
from secret import TOKEN
from commands import commandList

# Бот, который работает только с командами приложения
bot = commands.InteractionBot(intents=disnake.Intents.all())

# Парсим команды через цикл. Команды делаются через классы
for command in commandList:
    bot.add_slash_command(command)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} готов!")

bot.run(TOKEN)

import disnake
from disnake.ext import commands
import logging
from argparser import args
from log import setup_logger
import os
from dotenv import load_dotenv
load_dotenv()
setup_logger()

from voting import VotingMaker
from database import Database
from commands import Commons
from admins import Admins
from activity_tasks import ActivityTasks

from views import *
from embeds import *

token = None
if args.token is None:
    token = os.getenv("TOKEN")
else:
    token = args.token

if token is None:
    raise ValueError(f"Токен не обнаружен")
else:
    logger.info(f"Токен [{token[:5]}...] используется")

logger = logging.getLogger(__name__)

# Бот, который работает только с командами приложения
class Bot(commands.InteractionBot):
    def __init__(self) -> None:
        super().__init__(intents=disnake.Intents.all())

        logger.debug(f"Регистрация кога Commons")
        self.add_cog(Commons())
        logger.debug(f"Регистрация кога Admins")
        self.add_cog(Admins())

    async def on_ready(self) -> None:
        logger.info(f"Бот {self.user} готов!")
        self.database = await Database.open(args.database)
        self.voting = VotingMaker(self.database)
        self.add_cog(ActivityTasks(self))

        self.error_webhook = None
        if args.webhook is not None:
            try:
                self.error_webhook = await self.fetch_webhook(args.webhook)
                logger.info(f"Вебхук {args.webhook} успешно захвачен")
            except disnake.NotFound:
                logger.warning(f"Не удалось найти вебхук с ID {args.webhook}. Проигнорируется")
            except disnake.HTTPException as e:
                logger.warning(f"Не удалось захватить вебхук {args.webhook} по причине {e.text}. Проигнорируется")
            else:
                await self.error_webhook.send(
                    content=f"Бот {self.user.mention} запущен",
                    username=self.user.display_name + " Errors",
                    avatar_url=self.user.display_avatar.url
                )
        else:
            logger.info("Вебхук не используется")

    async def on_slash_command_error(self, inter: disnake.CommandInter, error: commands.CommandError) -> None:
        command = inter.application_command
        
        if self.error_webhook is not None:
            embed = ErrorEmbed(inter, self, error)
            await self.error_webhook.send(
                username=self.user.display_name + " Errors",
                avatar_url=self.user.display_avatar.url,
                embed=embed
            )
        
        logger.error(
            f"При выполнении команды [{command.qualified_name}] для {inter.author.name} проигнорирована ошибка:",
            exc_info=(type(error), error, error.__traceback__)
        )

    async def on_slash_command(self, inter: disnake.CommandInter) -> None:
        params = list(f"{k}: {v}" for k, v in inter.filled_options.items())
        t = [f"{inter.author.name} запросил комманду [{inter.application_command.qualified_name}]"]
        if len(params) != 0:
            t.append(f"с параметрами {', '.join(params)}")
        logger.info(" ".join(t))

    async def on_slash_command_completion(self, inter: disnake.CommandInter) -> None:
        params = list(f"{k}: {v}" for k, v in inter.filled_options.items())
        t = [f"Для {inter.author.name} команда [{inter.application_command.qualified_name}] была выполнена успешно"]
        if len(params) != 0:
            t.append(f"с параметрами {', '.join(params)}")
        logger.info(" ".join(t))

    async def vote(self, inter: disnake.Interaction, voting: VotingMaker.Voting, type_: bool, label: str) -> None:
        user = inter.author
        vote = await bot.voting.get_vote(inter.author.id, voting.id)
        t: bool | None = None
        if vote is not None:
            t = vote.type

        if voting.closed is not None:
            await inter.send(f"Голосование закрыто", ephemeral=True)
            return
        
        if inter.author.id == voting.author_id and not inter.permissions.administrator:
            await inter.send(f"Вы не можете проголосовать так как являетесь создателем голосования", ephemeral=True)
            return

        if t == type_:
            await inter.send(f"Вы уже проголосовали за {label}", ephemeral=True)
            return
        logger.info(f"{user.name} прологосовал за \"{label}\" в голосовании №{voting.id}: {voting.title}")
        
        await inter.send(f"Вы проголосовали за {label}", ephemeral=True)
        await bot.voting.create_vote(inter.author.id, voting.id, type_)

    async def stop_voting(self, inter: disnake.Interaction, voting: VotingMaker.Voting, send_embed: bool = False) -> None:
        if voting.closed is not None:
            await inter.send("Голосование уже было закрыто", ephemeral=True)
            return
        
        tasks: ActivityTasks = self.get_cog("ActivityTasks")

        if inter.permissions.administrator or inter.author.id == voting.author_id:
            await tasks.delete_voting_life(voting.id)
            await bot.voting.close_voting(voting.id)
            logger.info(f"{inter.author.name} окончил голосование №{voting.id}")
            if send_embed:
                count = await bot.voting.get_votes(voting.id)
                embed = ResultsEmbed(
                    await bot.fetch_user(voting.author_id),
                    voting,
                    count
                )
                await inter.send(embed=embed)
        else:
            await inter.send("У вас нет прав чтобы закрыть голосование", ephemeral=True)

    async def sign(self, inter: disnake.Interaction, petition: VotingMaker.Petition):
        user = inter.author
        sign = await bot.voting.get_sign(inter.author.id, petition.id)

        if petition.closed is not None:
            await inter.send(f"Петиция закрыта", ephemeral=True)
            return
        
        if inter.author.id == petition.author_id and not inter.permissions.administrator:
            await inter.send(f"Вы не можете подписать так как являетесь создателем петиции", ephemeral=True)
            return

        if sign is not None:
            await inter.send(f"Вы уже подписывали петицию", ephemeral=True)
            return
        logger.info(f"{user.name} подписал петицию №{petition.id}: {petition.title}")
        
        await inter.send(f"Вы подписали петицию", ephemeral=True)
        await bot.voting.create_sign(inter.author.id, petition.id)

    async def stop_petition(self, inter: disnake.Interaction, petition: VotingMaker.Petition, send_embed: bool = False) -> None:
        await bot.voting.get_petition(petition.id)
        if petition.closed is not None:
            await inter.send("Петиция уже была закрыта", ephemeral=True)
            return
        
        tasks: ActivityTasks = self.get_cog("ActivityTasks")

        if inter.permissions.administrator or inter.author.id == petition.author_id:
            await tasks.delete_petition_life(petition.id)
            petition = await bot.voting.close_petition(petition.id)
            logger.info(f"{inter.author.name} окончил петицию №{petition.id}")
            signs_count = await bot.voting.get_signs(petition.id)
            if send_embed:
                embed = ResultsEmbed(
                    await bot.fetch_user(petition.author_id),
                    petition,
                    signs_count
                )
                await inter.send(embed=embed)
        else:
            await inter.send("У вас нет прав чтобы закрыть петицию", ephemeral=True)

bot = Bot()
bot.run(token)
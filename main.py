from aiohttp import ClientSession
import disnake
from disnake.ext import commands
import logging
from argparser import args
from log import setup_logger
setup_logger()

from voting import VotingMaker
from database import AsyncSQLiteDB
from commands import Commons
from admins import Admins
from activity_tasks import ActivityTasks

from views import *
from embeds import *

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
        self.database = await AsyncSQLiteDB.open(args.database)
        self.voting = VotingMaker(self.database)
        self.add_cog(ActivityTasks(self))

        self.error_webhook = None
        if args.error_webhook is not None:
            try:
                self.error_webhook = await self.fetch_webhook(args.error_webhook)
                logger.info(f"Вебхук исключений {args.error_webhook} успешно захвачен")
            except disnake.NotFound:
                logger.warning(f"Не удалось найти вебхук исключений с ID {args.error_webhook}. Проигнорируется")
            except disnake.HTTPException as e:
                logger.warning(f"Не удалось захватить вебхук исключений {args.error_webhook} по причине {e.text}. Проигнорируется")
        else:
            logger.info("Вебхук исключений не используется")

        self.info_webhook = None
        if args.info_webhook is not None:
            try:
                self.info_webhook = await self.fetch_webhook(args.info_webhook)
                logger.info(f"Информационный вебхук {args.info_webhook} успешно захвачен")
            except disnake.NotFound:
                logger.warning(f"Не удалось найти информационный вебхук с ID {args.info_webhook}. Проигнорируется")
            except disnake.HTTPException as e:
                logger.warning(f"Не удалось захватить информационный вебхук {args.info_webhook} по причине {e.text}. Проигнорируется")
        else:
            logger.info("Информационный вебхук не используется")

    async def on_slash_command_error(self, inter: disnake.CommandInter, error: commands.CommandError) -> None:
        command = inter.application_command
        
        await self.send_error_webhook(embed=ErrorEmbed(inter, self, error))

        logger.error(
            f"При выполнении команды [{command.qualified_name}] для {inter.author.name} проигнорирована ошибка:",
            exc_info=(type(error), error, error.__traceback__)
        )

    async def on_slash_command(self, inter: disnake.CommandInter) -> None:
        params = list(f"{k}: {v}" for k, v in inter.filled_options.items())
        t = [f"{inter.author.name} запросил комманду [{inter.application_command.qualified_name}]"]
        wt = [f"{inter.author.mention} запросил команду `{inter.application_command.qualified_name}`"]
        if len(params) != 0:
            t.append(f"с параметрами {', '.join(params)}")
            wt.append(f"с параметрами `{', '.join(params)}`")
        await self.send_info_webhook(content=" ".join(wt))
        logger.info(" ".join(t))

    async def on_slash_command_completion(self, inter: disnake.CommandInter) -> None:
        params = list(f"{k}: {v}" for k, v in inter.filled_options.items())
        t = [f"Для {inter.author.name} команда [{inter.application_command.qualified_name}] была выполнена успешно"]
        if len(params) != 0:
            t.append(f"с параметрами {', '.join(params)}")
        logger.info(" ".join(t))

    async def _send_webhook(self, webhook: disnake.Webhook, suffix: str = "", **kwargs) -> None:
        await webhook.send(
            username=self.user.display_name+" "+suffix,
            avatar_url=self.user.display_avatar.url,
            allowed_mentions=disnake.AllowedMentions.none(),
            **kwargs
        )

    async def send_error_webhook(self, **kwargs) -> None:
        if self.error_webhook is not None:
            await self._send_webhook(self.error_webhook, "Errors", **kwargs)

    async def send_info_webhook(self, **kwargs) -> None:
        if self.info_webhook is not None:
            await self._send_webhook(self.info_webhook, "Information", **kwargs)

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
        await self.send_info_webhook(content=f"{user.mention} прологосовал за \"{label}\" в голосовании №{voting.id}: {voting.title}")
        
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
            await self.send_info_webhook(content=f"{inter.author.mention} окончил голосование №{voting.id}")
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
        await self.send_info_webhook(content=f"{user.mention} подписал петицию №{petition.id}: {petition.title}")
        
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
            await self.send_info_webhook(content=f"{inter.author.mention} окончил петицию №{petition.id}")
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
if (token := args.token) is None:
    raise ValueError("Токен не обнаружен")
else:
    logger.info(f"Токен [{token[:5]}...] используется")
bot.run(token)
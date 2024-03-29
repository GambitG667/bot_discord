from __future__ import annotations
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from dataclasses import dataclass

import logging
logger = logging.getLogger(__name__)

from embeds import ResultsEmbed

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Bot

class ActivityTasks(commands.Cog):
    @dataclass
    class VotingLife:
        voting_id: int
        death: datetime
        channel_id: int

    @dataclass
    class PetitionLife:
        petition_id: int
        death: datetime
        channel_id: int

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.db = bot.database
        self.check_activity_life.start()

    async def get_activity_lifes(self) -> tuple[VotingLife | PetitionLife, ...]:
        query = "SELECT \"voting\", * FROM voting_life UNION ALL SELECT \"petition\", * FROM petition_life"
        t = await self.db.async_get(query, tuple())
        clss = {"voting": self.VotingLife, "petition": self.PetitionLife}
        for i, a in enumerate(t):
            t[i] = clss[a[0]](*a[1:])
        return tuple(t)
    
    async def _delete_activity_life(self, table: str, id_name: str, id_: int) -> int:
        query = f"DELETE FROM {table} WHERE {id_name}=?"
        return await self.db.async_put(query, (id_,))
    
    async def delete_voting_life(self, voting_id: int) -> int:
        return await self._delete_activity_life("voting_life", "voting_id", voting_id)
    
    async def delete_petition_life(self, petition_id: int) -> int:
        return await self._delete_activity_life("petition_life", "petition_id", petition_id)
    
    async def create_voting_life(self, voting_id: int, channel_id, td: timedelta) -> int:
        query = "INSERT INTO voting_life (voting_id,channel_id,death) VALUES (?, ?, ?)"
        dt = datetime.today() + td
        return await self.db.async_put(query, (voting_id, channel_id, dt))
    
    async def create_petition_life(self, petition_id: int, channel_id, td: timedelta) -> int:
        query = "INSERT INTO petition_life (petition_id,channel_id,death) VALUES (?, ?, ?)"
        dt = datetime.today() + td
        return await self.db.async_put(query, (petition_id, channel_id, dt))

    @tasks.loop(seconds=10)
    async def check_activity_life(self) -> None:
        for a in await self.get_activity_lifes():
            if isinstance(a, self.VotingLife):
                activity = await self.bot.voting.get_voting(a.voting_id)
            else:
                activity = await self.bot.voting.get_petition(a.petition_id)

            if activity is not None:
                if a.death <= datetime.now():
                    if isinstance(a, self.VotingLife):
                        await self.bot.voting.close_voting(a.voting_id)
                        await self.delete_voting_life(a.voting_id)
                        logger.info(f"Голосование №{a.voting_id} было успешно завершено")
                        embed = ResultsEmbed(
                            await self.bot.fetch_user(activity.author_id),
                            activity,
                            await self.bot.voting.get_votes(a.voting_id)
                        )
                    else:
                        await self.bot.voting.close_petition(a.petition_id)
                        await self.delete_petition_life(a.petition_id)
                        logger.info(f"Петиция №{a.voting_id} была успешно завершена")
                        embed = ResultsEmbed(
                            await self.bot.fetch_user(activity.author_id),
                            activity,
                            await self.bot.voting.get_sign(a.petition_id)
                        )
                    channel = await self.bot.fetch_channel(a.channel_id)
                    await channel.send(embed=embed)
            else:
                if isinstance(a, self.VotingLife):
                    id_ = a.voting_id
                    await self.delete_voting_life(id_)
                else:
                    id_ = a.petition_id
                    await self.delete_petition_life(id_)
                logger.warning(f"Активности №{id_} не существует чтобы проверять его жизненный цикл. Его запись будет удалена")

    @check_activity_life.before_loop
    async def before_activity_check(self) -> None:
        await self.bot.wait_until_ready()
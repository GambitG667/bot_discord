from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database import Database

class Voting:
    @dataclass
    class Voting:
        id: int
        title: str
        description: str
        author_id: int
        anonym: bool
        created: datetime
        closed: datetime | None

    @dataclass
    class Vote:
        id: int
        user_id: int
        voting_id: int
        type: bool
        created: datetime

    @dataclass
    class VoteWithIndex:
        index: int
        vote: Voting.Vote

    def __init__(self, db: Database):
        self.db = db

    async def start_voting(self, title: str, desc: str, author_id: int, anonym: bool) -> int:
        query = "INSERT INTO votings (title,description,author_id,created,anonym) VALUES (?, ?, ?, ?, ?)"
        return await self.db.async_put(query, (title, desc, author_id, datetime.today(), anonym))

    async def close_voting(self, id_: int) -> int:
        query = "UPDATE votings SET closed = ? WHERE id = ?"
        return await self.db.async_put(query, (datetime.today(), id_))

    async def get_voting(self, id_: int) -> Voting:
        query = "SELECT * FROM votings WHERE id = ?"
        t = await self.db.async_get_one(query, (id_,))
        if t is not None:
            return self.Voting(*t)
        
    async def get_votings_list(self, start) -> list[Voting.Voting]:
        query = "SELECT * FROM votings ORDER BY created DESC LIMIT ?, 21"
        t = await self.db.async_get(query, (start,))
        for i, voting in enumerate(t):
            t[i] = self.Voting(*voting)
        return t

    async def create_vote(self, user_id: int, voting_id: int, type_: bool) -> int:
        query = "INSERT INTO votes (user_id,voting_id,type,created) VALUES (?, ?, ?, ?)"
        return await self.db.async_put(query, (user_id, voting_id, type_, datetime.today()))

    async def get_vote(self, user_id: int, voting_id: int) -> Vote:
        query = "SELECT * FROM votes WHERE user_id = ? AND voting_id = ? ORDER BY id DESC"
        t = await self.db.async_get_one(query, (user_id, voting_id))
        if t is not None:
            return self.Vote(*t)

    async def get_vote_by_id(self, id_: int) -> Vote:
        query = "SELECT * FROM votes WHERE id = ?"
        t = await self.db.async_get_one(query, (id_,))
        if t is not None:
            return self.Vote(*t)
        
    async def get_votes(self, voting_id: int) -> tuple[bool, bool]:
        query = "SELECT type, count(*) FROM (SELECT type FROM votes  WHERE voting_id = ? GROUP BY user_id HAVING max(created)) GROUP BY type"
        t = await self.db.async_get(query, (voting_id,))
        for_ = 0
        against = 0
        for v in t:
            match v[0]:
                case 0:
                    against = v[1]
                case 1:
                    for_ = v[1]
        return against, for_
    
    async def get_votes_list(self, voting_id: int, start: int) -> list[Voting.VoteWithIndex]:
        query = "SELECT * FROM votes WHERE voting_id = ? ORDER BY created DESC LIMIT ?, 21"
        t = await self.db.async_get(query, (voting_id, start))
        for i, vote in enumerate(t):
            t[i] = Voting.VoteWithIndex(start + i + 1, self.Vote(*vote))
        return t
from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database import Database

class VotingMaker:
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
        vote: VotingMaker.Vote

    @dataclass
    class VotesCount:
        to: int
        against: int

    @dataclass
    class Petition:
        id: int
        title: str
        description: str
        author_id: int
        anonym: bool
        created: datetime
        closed: datetime | None

    @dataclass
    class Sign:
        id: int
        user_id: int
        voting_id: int
        created: datetime

    @dataclass
    class SignWithIndex:
        index: int
        sign: VotingMaker.Sign

    @dataclass
    class SignsCount:
        count: int

    def __init__(self, db: Database):
        self.db = db

    async def start_voting(self, title: str, desc: str, author_id: int, anonym: bool) -> Voting:
        query = "INSERT INTO votings (title,description,author_id,created,anonym) VALUES (?, ?, ?, ?, ?)"
        id_ = await self.db.async_put(query, (title, desc, author_id, datetime.today(), anonym))
        return await self.get_voting(id_)

    async def close_voting(self, id_: int) -> Voting:
        query = "UPDATE votings SET closed = ? WHERE id = ?"
        id_ = await self.db.async_put(query, (datetime.today(), id_))
        return await self.get_voting(id_)

    async def get_voting(self, id_: int) -> Voting | None:
        query = "SELECT * FROM votings WHERE id = ?"
        t = await self.db.async_get_one(query, (id_,))
        if t is not None:
            return self.Voting(*t)
        
    async def get_votings_list(self, start) -> list[Voting]:
        query = "SELECT * FROM votings ORDER BY created DESC LIMIT ?, 21"
        t = await self.db.async_get(query, (start,))
        for i, voting in enumerate(t):
            t[i] = self.Voting(*voting)
        return t

    async def create_vote(self, user_id: int, voting_id: int, type_: bool) -> Vote:
        query = "INSERT INTO votes (user_id,voting_id,type,created) VALUES (?, ?, ?, ?)"
        id_ = await self.db.async_put(query, (user_id, voting_id, type_, datetime.today()))
        return await self.get_vote_by_id(id_)

    async def get_vote(self, user_id: int, voting_id: int) -> Vote | None:
        query = "SELECT * FROM votes WHERE user_id = ? AND voting_id = ? ORDER BY id DESC"
        t = await self.db.async_get_one(query, (user_id, voting_id))
        if t is not None:
            return self.Vote(*t)

    async def get_vote_by_id(self, id_: int) -> Vote | None:
        query = "SELECT * FROM votes WHERE id = ?"
        t = await self.db.async_get_one(query, (id_,))
        if t is not None:
            return self.Vote(*t)
        
    async def get_votes(self, voting_id: int) -> VotesCount:
        query = "SELECT type, count(*) FROM (SELECT type FROM votes WHERE voting_id = ? GROUP BY user_id HAVING max(created)) GROUP BY type"
        t = await self.db.async_get(query, (voting_id,))
        for_ = 0
        against = 0
        for v in t:
            match v[0]:
                case 0:
                    against = v[1]
                case 1:
                    for_ = v[1]
        return self.VotesCount(for_, against)
    
    async def get_votes_list(self, voting_id: int, start: int) -> list[VoteWithIndex]:
        query = "SELECT * FROM votes WHERE voting_id = ? ORDER BY created DESC LIMIT ?, 21"
        t = await self.db.async_get(query, (voting_id, start))
        for i, vote in enumerate(t):
            t[i] = self.VoteWithIndex(start + i + 1, self.Vote(*vote))
        return t
    
    async def start_petition(self, title: str, desc: str, author_id: int, anonym: bool) -> Petition:
        query = "INSERT INTO petitions (title,description,author_id,created,anonym) VALUES (?, ?, ?, ?, ?)"
        id_ = await self.db.async_put(query, (title, desc, author_id, datetime.today(), anonym))
        return await self.get_petition(id_)

    async def close_petition(self, id_: int) -> Petition:
        query = "UPDATE petitions SET closed = ? WHERE id = ?"
        id_ = await self.db.async_put(query, (datetime.today(), id_))
        return await self.get_petition(id_)

    async def get_petition(self, id_: int) -> Petition | None:
        query = "SELECT * FROM petitions WHERE id = ?"
        t = await self.db.async_get_one(query, (id_,))
        if t is not None:
            return self.Petition(*t)
        
    async def get_petitions_list(self, start) -> list[Petition]:
        query = "SELECT * FROM petitions ORDER BY created DESC LIMIT ?, 21"
        t = await self.db.async_get(query, (start,))
        for i, petition in enumerate(t):
            t[i] = self.Petition(*petition)
        return t

    async def create_sign(self, user_id: int, petition_id: int) -> Sign:
        query = "INSERT INTO signs (user_id,petition_id,created) VALUES (?, ?, ?)"
        id_ = await self.db.async_put(query, (user_id, petition_id, datetime.today()))
        return await self.get_sign_by_id(id_)

    async def get_sign(self, user_id: int, petition_id: int) -> Sign | None:
        query = "SELECT * FROM signs WHERE user_id = ? AND petition_id = ? ORDER BY id DESC"
        t = await self.db.async_get_one(query, (user_id, petition_id))
        if t is not None:
            return self.Sign(*t)

    async def get_sign_by_id(self, id_: int) -> Sign | None:
        query = "SELECT * FROM signs WHERE id = ?"
        t = await self.db.async_get_one(query, (id_,))
        if t is not None:
            return self.Sign(*t)
        
    async def get_signs(self, petition_id: int) -> SignsCount:
        query = "SELECT count(*) FROM (SELECT id FROM signs WHERE petition_id = ? GROUP BY user_id HAVING max(created))"
        t = await self.db.async_get_one(query, (petition_id,))
        return self.SignsCount(t[0])
    
    async def get_signs_list(self, petition_id: int, start: int) -> list[SignWithIndex]:
        query = "SELECT * FROM signs WHERE petition_id = ? ORDER BY created DESC LIMIT ?, 21"
        t = await self.db.async_get(query, (petition_id, start))
        for i, sign in enumerate(t):
            t[i] = self.SignWithIndex(start + i + 1, self.Sign(*sign))
        return t
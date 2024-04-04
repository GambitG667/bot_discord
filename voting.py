from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field

from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from database import AsyncSQLiteDB

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

        def __str__(self):
            return "голосование"

    @dataclass
    class Vote:
        id: int
        user_id: int
        voting_id: int
        type: bool
        created: datetime

        def __str__(self):
            return "голос"

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

        def __str__(self):
            return "петиция"

    @dataclass
    class Sign:
        id: int
        user_id: int
        petition_id: int
        created: datetime

        def __str__(self):
            return "подпись"

    @dataclass
    class SignsCount:
        count: int

    @staticmethod
    async def _map_list(t: list[list[any]], cls: type[Voting | Vote | Petition | Sign]) -> None:
        for i, sth in enumerate(t):
            t[i] = cls(*sth)

    def __init__(self, db: AsyncSQLiteDB):
        self.db = db

    async def start_voting(self, title: str, desc: str, author_id: int, anonym: bool) -> Voting:
        query = "INSERT INTO votings (title,description,author_id,created,anonym) VALUES (?, ?, ?, ?, ?)"
        id_ = await self.db.async_operate(query, (title, desc, author_id, datetime.today(), anonym))
        return await self.get_voting(id_)

    async def close_voting(self, id_: int) -> Voting:
        query = "UPDATE votings SET closed = ? WHERE id = ?"
        id_ = await self.db.async_operate(query, (datetime.today(), id_))
        return await self.get_voting(id_)
    
    async def delete_voting(self, id_: int) -> None:
        query = "DELETE FROM votings WHERE id = ?"
        await self.db.async_operate(query, (id_,))

    async def get_voting(self, id_: int) -> Voting | None:
        query = "SELECT * FROM votings WHERE id = ?"
        t = await self.db.async_fetchone(query, (id_,))
        if t is not None:
            return self.Voting(*t)
        
    async def get_votings_list(self, start) -> list[Voting]:
        query = "SELECT * FROM votings ORDER BY id DESC LIMIT ?, 21"
        t = await self.db.async_fetchall(query, (start,))
        await self._map_list(t, self.Voting)
        return t

    async def create_vote(self, user_id: int, voting_id: int, type_: bool) -> Vote:
        query = "INSERT INTO votes (user_id,voting_id,type,created) VALUES (?, ?, ?, ?)"
        id_ = await self.db.async_operate(query, (user_id, voting_id, type_, datetime.today()))
        return await self.get_vote_by_id(id_)

    async def get_vote(self, user_id: int, voting_id: int) -> Vote | None:
        query = "SELECT * FROM votes WHERE user_id = ? AND voting_id = ? ORDER BY id DESC LIMIT 1"
        t = await self.db.async_fetchone(query, (user_id, voting_id))
        if t is not None:
            return self.Vote(*t)

    async def get_vote_by_id(self, id_: int) -> Vote | None:
        query = "SELECT * FROM votes WHERE id = ?"
        t = await self.db.async_fetchone(query, (id_,))
        if t is not None:
            return self.Vote(*t)
        
    async def get_votes(self, voting_id: int) -> VotesCount:
        query = "SELECT type, count(*) FROM (SELECT type FROM votes WHERE voting_id = ? GROUP BY user_id HAVING max(id)) GROUP BY type"
        t = await self.db.async_fetchall(query, (voting_id,))
        for_ = 0
        against = 0
        for v in t:
            match v[0]:
                case 0:
                    against = v[1]
                case 1:
                    for_ = v[1]
        return self.VotesCount(for_, against)
    
    async def get_votes_list(self, voting_id: int, start: int) -> list[Vote]:
        query = "SELECT * FROM votes WHERE voting_id = ? ORDER BY id DESC LIMIT ?, 21"
        t = await self.db.async_fetchall(query, (voting_id, start))
        await self._map_list(t, self.Vote)
        return t
    
    async def get_votings_list_by_user(self, user_id: int, start: int) -> list[Voting]:
        query = "SELECT * FROM votings WHERE author_id = ? ORDER BY id DESC LIMIT ?, 21"
        t = await self.db.async_fetchall(query, (user_id, start))
        await self._map_list(t, self.Voting)
        return t
    
    async def get_votes_list_by_user(self, user_id: int, start: int) -> list[Vote]:
        query = "SELECT * FROM votes WHERE user_id = ? GROUP BY voting_id HAVING max(id) ORDER BY id DESC LIMIT ?, 21"
        t = await self.db.async_fetchall(query, (user_id, start))
        await self._map_list(t, self.Vote)
        return t
    
    async def start_petition(self, title: str, desc: str, author_id: int, anonym: bool) -> Petition:
        query = "INSERT INTO petitions (title,description,author_id,created,anonym) VALUES (?, ?, ?, ?, ?)"
        id_ = await self.db.async_operate(query, (title, desc, author_id, datetime.today(), anonym))
        return await self.get_petition(id_)

    async def close_petition(self, id_: int) -> Petition:
        query = "UPDATE petitions SET closed = ? WHERE id = ?"
        id_ = await self.db.async_operate(query, (datetime.today(), id_))
        return await self.get_petition(id_)
    
    async def delete_petition(self, id_: int) -> None:
        query = "DELETE FROM petitions WHERE id = ?"
        await self.db.async_operate(query, (id_,))

    async def get_petition(self, id_: int) -> Petition | None:
        query = "SELECT * FROM petitions WHERE id = ?"
        t = await self.db.async_fetchone(query, (id_,))
        if t is not None:
            return self.Petition(*t)
        
    async def get_petitions_list(self, start) -> list[Petition]:
        query = "SELECT * FROM petitions ORDER BY id DESC LIMIT ?, 21"
        t = await self.db.async_fetchall(query, (start,))
        await self._map_list(t, self.Petition)
        return t

    async def create_sign(self, user_id: int, petition_id: int) -> Sign:
        query = "INSERT INTO signs (user_id,petition_id,created) VALUES (?, ?, ?)"
        id_ = await self.db.async_operate(query, (user_id, petition_id, datetime.today()))
        return await self.get_sign_by_id(id_)

    async def get_sign(self, user_id: int, petition_id: int) -> Sign | None:
        query = "SELECT * FROM signs WHERE user_id = ? AND petition_id = ? ORDER BY id DESC LIMIT 1"
        t = await self.db.async_fetchone(query, (user_id, petition_id))
        if t is not None:
            return self.Sign(*t)

    async def get_sign_by_id(self, id_: int) -> Sign | None:
        query = "SELECT * FROM signs WHERE id = ?"
        t = await self.db.async_fetchone(query, (id_,))
        if t is not None:
            return self.Sign(*t)
        
    async def get_signs(self, petition_id: int) -> SignsCount:
        query = "SELECT count(*) FROM (SELECT id FROM signs WHERE petition_id = ? GROUP BY user_id HAVING max(created))"
        t = await self.db.async_fetchone(query, (petition_id,))
        return self.SignsCount(t[0])
    
    async def get_signs_list(self, petition_id: int, start: int) -> list[Sign]:
        query = "SELECT * FROM signs WHERE petition_id = ? ORDER BY id DESC LIMIT ?, 21"
        t = await self.db.async_fetchall(query, (petition_id, start))
        await self._map_list(t, self.Sign)
        return t
    
    async def get_petitions_list_by_user(self, user_id: int, start: int) -> list[Petition]:
        query = "SELECT * FROM petitions WHERE author_id = ? ORDER BY id DESC LIMIT ?, 21"
        t = await self.db.async_fetchall(query, (user_id, start))
        await self._map_list(t, self.Petition)
        return t
    
    async def get_signs_list_by_user(self, user_id: int, start: int) -> list[Sign]:
        query = "SELECT * FROM signs WHERE user_id = ? GROUP BY petition_id HAVING max(id) ORDER BY id DESC LIMIT ?, 21"
        t = await self.db.async_fetchall(query, (user_id, start))
        await self._map_list(t, self.Sign)
        return t
    
    async def get_activities_by_user(self, user_id: int, start: int, filter: Literal["голосования", "петиции", "все"]) -> list[Voting | Petition]:
        if filter == "голосования":
            return await self.get_votings_list_by_user(user_id, start)
        elif filter == "петиции":
            return await self.get_petitions_list_by_user(user_id, start)
        else:
            query = "SELECT \"voting\", * FROM votings WHERE author_id = ? UNION ALL SELECT \"petition\", * FROM petitions WHERE author_id = ? ORDER BY created DESC LIMIT ?, 21"
            t = await self.db.async_fetchall(query, (user_id, user_id, start))
            clss = {"voting": self.Voting, "petition": self.Petition}
            for i, sth in enumerate(t):
                t[i] = clss[sth[0]](*sth[1:])
            return t
    
    async def get_actives_by_user(self, user_id: int, start: int, filter: Literal["голоса", "подписи", "все"], admin: bool) -> list[Vote | Sign]:
        if filter == "голоса":
            return await self.get_votes_list_by_user(user_id, start)
        elif filter == "подписи":
            return await self.get_signs_list_by_user(user_id, start)
        else:
            query1 = "SELECT \"vote\", votes.id, user_id, voting_id, type, votes.created as created FROM votes JOIN votings ON votings.id = votes.voting_id WHERE user_id = ? AND votings.anonym = 0 GROUP BY voting_id HAVING max(votes.id) UNION ALL SELECT \"sign\", signs.id, user_id, petition_id, NULL, signs.created FROM signs JOIN petitions ON petitions.id = signs.petition_id WHERE user_id = ? AND petitions.anonym = 0 GROUP BY petition_id HAVING max(signs.id) ORDER BY created DESC LIMIT ?, 21"
            query2 = "SELECT \"vote\", id, user_id, voting_id, type, created FROM votes WHERE user_id = ? GROUP BY voting_id HAVING max(id) UNION ALL SELECT \"sign\", id, user_id, petition_id, NULL, created FROM signs WHERE user_id = ? GROUP BY petition_id HAVING max(id) ORDER BY created DESC LIMIT ?, 21"
            query = query2 if admin else query1
            t = await self.db.async_fetchall(query, (user_id, user_id, start))
            clss = {"vote": self.Vote, "sign": self.Sign}
            for i, sth in enumerate(t):
                if sth[0] == "sign":
                    t[i] = clss[sth[0]](*(sth[1:4]+sth[5:]))
                else:
                    t[i] = clss[sth[0]](*sth[1:])
            return t
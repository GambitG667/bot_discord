from datetime import datetime
from dataclasses import dataclass

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

    def __init__(self, db):
        self.db = db

    async def start_voting(self, title, desc, author_id, anonym):
        query = "INSERT INTO votings (title,description,author_id,created,anonym) VALUES (?, ?, ?, ?, ?)"
        return await self.db.async_put(query, (title, desc, author_id, datetime.today(), anonym))

    async def close_voting(self, id_):
        query = "UPDATE votings SET closed = ? WHERE id = ?"
        return await self.db.async_put(query, (datetime.today(), id_))

    async def get_voting(self, id_):
        query = "SELECT * FROM votings WHERE id = ?"
        t = await self.db.async_get_one(query, (id_,))
        if t is not None:
            return self.Voting(*t)

    async def create_vote(self, user_id, voting_id, type_):
        query = "INSERT INTO votes (user_id,voting_id,type,created) VALUES (?, ?, ?, ?)"
        return  await self.db.async_put(query, (user_id, voting_id, type_, datetime.today()))

    async def get_vote(self, user_id, voting_id):
        query = "SELECT * FROM votes WHERE user_id = ? AND voting_id = ? ORDER BY id DESC"
        t = await self.db.async_get_one(query, (user_id, voting_id))
        if t is not None:
            return self.Vote(*t)

    async def get_vote_by_id(self, id_):
        query = "SELECT * FROM votes WHERE id = ?"
        t = await self.db.async_get_one(query, (id_,))
        if t is not None:
            return self.Vote(*t)
        
    async def get_votes(self, voting_id):
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
    
    async def get_votes_list(self, voting_id, start):
        query = "SELECT * FROM votes WHERE voting_id = ? ORDER BY created DESC LIMIT ?, 21"
        t = await self.db.async_get(query, (voting_id, start))
        for i, vote in enumerate(t):
            t[i] = [start + i + 1, self.Vote(*vote)]
        return t
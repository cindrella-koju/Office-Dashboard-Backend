from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select
from models import Match
from exception import HTTPNotFound

async def extract_match_by_id(db:AsyncSession, match_id : UUID):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match_info = result.scalars().one_or_none()

    if not match_info:
        raise HTTPNotFound("Match not found")
    
    return match_info


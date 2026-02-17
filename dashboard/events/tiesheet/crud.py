from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select
from models import TiesheetPlayer, Tiesheet
from exception import HTTPNotFound

async def extract_tiesheet_player_by_tiesheet_id(db : AsyncSession, tiesheet_id : UUID):
    stmt = select(TiesheetPlayer).where(
        TiesheetPlayer.tiesheet_id == tiesheet_id
    )
    result = await db.execute(stmt)
    players = result.scalars().all()

    if not players:
        raise HTTPNotFound("No players found for this tiesheet")
    
    return players

async def get_tiesheet( db : AsyncSession, tiesheet_id : UUID):
    stmt = select(Tiesheet).where(Tiesheet.id == tiesheet_id)
    result = await db.execute(stmt)
    tiesheet = result.scalars().one_or_none()

    if not tiesheet:
        raise HTTPNotFound("Tiesheet not found")

    return tiesheet
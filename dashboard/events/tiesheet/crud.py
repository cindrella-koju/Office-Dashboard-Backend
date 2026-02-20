from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select, and_
from models import TiesheetPlayer, Tiesheet
from exception import HTTPNotFound
from typing import List

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

from sqlalchemy import select, func

async def check_tiesheet_exist(
    db: AsyncSession,
    players: list[UUID],
    stage_id: UUID,
) -> bool:

    if not players:
        return False

    stmt = (
        select(TiesheetPlayer.tiesheet_id, Tiesheet.stage_id, func.count(TiesheetPlayer.user_id).label("user_count"))
        .join(Tiesheet)
        .where(
            and_(
                TiesheetPlayer.user_id.in_(players),
                Tiesheet.stage_id == stage_id
            )
        )
        .group_by(TiesheetPlayer.tiesheet_id, Tiesheet.stage_id)
        .having(func.count(TiesheetPlayer.user_id) == len(players))
    )
    result = await db.execute(stmt)
    users = result.all()

    print
    return users

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select, and_, func, case
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


async def extract_tiesheet_player_by_tiesheetplayer_id(db : AsyncSession, tiesheetplayer_id : UUID):
    stmt = select(TiesheetPlayer).where(
        TiesheetPlayer.id == tiesheetplayer_id
    )
    result = await db.execute(stmt)
    players = result.one_or_none()

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

async def check_tiesheet_exist(
    db: AsyncSession,
    players: list[UUID],
    stage_id: UUID,
    tbd_number: int | None = None
) -> bool:

    if not players:
        return False

    stmt = (
        select(
            TiesheetPlayer.tiesheet_id,
            func.count(TiesheetPlayer.user_id).label("user_count"),
            func.sum(case((TiesheetPlayer.user_id == None, 1), else_=0)).label("tbd_count"),
            func.count(case((TiesheetPlayer.user_id.in_(players), 1))).label("matched_players")
        )
        .join(Tiesheet)
        .where(Tiesheet.stage_id == stage_id)
        .group_by(TiesheetPlayer.tiesheet_id)
        .having(func.count(case((TiesheetPlayer.user_id.in_(players), 1))) == len(players))
    )

    result = await db.execute(stmt)
    tiesheets = result.all()

    for tiesheet_id, user_count, tbd_count, matched_players in tiesheets:
        if tbd_number is not None:
            if tbd_count == tbd_number:
                return True
        else:
            return True


    return False


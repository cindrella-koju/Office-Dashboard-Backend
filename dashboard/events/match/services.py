from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import TiesheetPlayer
from sqlalchemy import select, and_

async def extract_tiesheet_player_id(db:AsyncSession,user_id : UUID, tiesheet_id : UUID):
    stmt = select(TiesheetPlayer.id).where(
        and_(
            TiesheetPlayer.tiesheet_id == tiesheet_id,
            TiesheetPlayer.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    tiesheetplayer_id = result.one_or_none()
    if tiesheetplayer_id is None:
        raise ValueError("Tiesheet player not available")

    return tiesheetplayer_id[0]
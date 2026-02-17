from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select
from models import Stage
from exception import HTTPNotFound

async def extract_stage_by_id( db:AsyncSession, stage_id : UUID ):
    result = await db.execute(select(Stage).where(Stage.id == stage_id).order_by(Stage.created_at))
    stage = result.scalar_one_or_none()

    if not stage:
        raise HTTPNotFound("Round not found")
    return stage

async def extract_stage_by_event(db:AsyncSession, event_id : UUID):
    result = await db.execute(select(Stage).where(Stage.event_id == event_id).order_by(Stage.created_at))
    stages = result.scalars().all()
    if not stages:
        raise HTTPNotFound("Stage not found")
    return stages
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import Event
from sqlalchemy import select

async def extract_event_by_id(db : AsyncSession, event_id : UUID):
    result = await db.execute(select(Event).where(Event.id == event_id))
    return result.scalars().first()
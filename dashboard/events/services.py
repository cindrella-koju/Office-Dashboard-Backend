from sqlalchemy.ext.asyncio import AsyncSession
from models import Event
from uuid import UUID
from sqlalchemy import select

async def extract_all_event(db: AsyncSession, status: str | None = None):
    if status is None or status.lower() == "all":
        result = await db.execute(select(Event))
    else:
        result = await db.execute(select(Event).where(Event.status == status.lower()))

    events = result.scalars().all()
    return events

async def extract_one_event(db:AsyncSession, event_id : UUID):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    return event
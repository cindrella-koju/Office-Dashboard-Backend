from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import UserRole
from exception import  HTTPNotFound
from sqlalchemy import select

async def extract_event_role_by_id(db : AsyncSession, event_role_id : UUID):
    stmt = await db.execute(select(UserRole).where(UserRole.id == event_role_id))
    event_role = stmt.scalars().one_or_none()

    if not event_role:
        raise HTTPNotFound("Event role not found")
    
    return event_role


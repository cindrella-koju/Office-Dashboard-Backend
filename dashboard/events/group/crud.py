from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select
from models import Group
from exception import HTTPNotFound

async def extract_group_by_id(db:AsyncSession, group_id : UUID):
    stmt = select(Group).where(Group.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPNotFound("Group not found")
    return group
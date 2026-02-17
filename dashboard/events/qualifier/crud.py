from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select
from models import Qualifier
from exception import HTTPNotFound

async def extract_qualifier_by_id(db:AsyncSession, qualifier_id : UUID):
    result = await db.execute(select(Qualifier).where(Qualifier.id == qualifier_id))
    qualifier = result.scalar_one_or_none()

    if not qualifier:
        raise HTTPNotFound("Qualifier not found")


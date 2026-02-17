from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select
from models import StandingColumn
from exception import HTTPNotFound

async def extract_column_by_id( db: AsyncSession, column_id : UUID):
    result = await db.execute(select(StandingColumn).where(StandingColumn.id == column_id))
    column = result.scalars().first()

    if not column:
        raise HTTPNotFound("Column not Found")
    
    return column
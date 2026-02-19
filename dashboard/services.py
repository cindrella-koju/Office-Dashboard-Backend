from sqlalchemy.ext.asyncio import AsyncSession

async def pagination(db : AsyncSession, page:int, limit : int, stmt):
    skip = (page -1) * limit
    
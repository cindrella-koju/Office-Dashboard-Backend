from models import Role
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_member_role_id(db: AsyncSession):
    """"
        extract the id of role member
    """
    stmt = select(Role.id).where(Role.rolename.ilike("member"))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
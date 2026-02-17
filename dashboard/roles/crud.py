from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import UserRole, Role
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_user_role(
    db : AsyncSession,
    user_id : UUID
):
    """ Extract user Role """
    role_info = await db.execute(select(UserRole).where(UserRole.user_id == user_id))
    return role_info.scalars().first()

async def get_role_by_id( db : AsyncSession, role_id : UUID):
    """ Extract role detail by role_id"""
    stmt = select(Role).options(selectinload(Role.roleaccesspage)).where(Role.id == role_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
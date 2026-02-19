from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from models import User, Role, UserRole
from uuid import UUID
from users.schema import UserDetailResponse
from sqlalchemy.orm import selectinload

async def get_user_by_email_or_username(
    db: AsyncSession,
    email: str | None = None,
    username: str | None = None
):
    """
    Extract user by email or username
    """
    conditions = []
    if email is not None:
        conditions.append(User.email == email)
    if username is not None:
        conditions.append(User.username == username)
    
    if not conditions:
        return None
    stmt = select(User).where(or_(*conditions))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_role(db: AsyncSession,page : int, limit : int,role_id : UUID | None = None):
    """"
        Extract user detail with role info
    """
    skip = (page - 1) * limit
    stmt = (
        select(
            User.id.label("id"),
            User.username,
            User.fullname,
            User.email,
            Role.id.label("role_id"),
            Role.rolename
        )
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, UserRole.role_id == Role.id)
        .where(UserRole.event_id.is_(None))
    )

    if role_id:
        stmt = stmt.where(UserRole.role_id == role_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    user = result.mappings().all()

    count_stmt = select(func.count()).select_from(User)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()    

    return {
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "items": [UserDetailResponse.model_validate(u) for u in user]
    }

async def get_all_users(db : AsyncSession, role_id : str | None = None):
    """Extract all user detail"""
    if role_id is None or role_id.lower() == "all":
        result = await db.execute(select(User))
    else:
        result = await db.execute(select(User).where(User.role == role_id.lower()))
    users = result.scalars().all()
    return [ UserDetailResponse.model_validate(user) for user in users]

async def get_user_with_roles_by_username(
    db: AsyncSession,
    username: str
):
    """ Extract user with role """
    stmt = (
        select(User)
        .options(
            selectinload(User.userrole)
            .selectinload(UserRole.role)
        )
        .where(User.username == username)
    )

    result = await db.execute(stmt)
    return result.scalars().first()

async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID  
):
    """ Extract single user by user_id """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_user_with_roles_by_id(
    db: AsyncSession,
    user_id: UUID
):
    """ Extract user with role by user_id """
    stmt = (
        select(User)
        .options(
            selectinload(User.userrole)
            .selectinload(UserRole.role)
        )
        .where(User.id == user_id)
    )

    result = await db.execute(stmt)
    return result.scalars().first()
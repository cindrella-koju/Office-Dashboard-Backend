from models import Role, RoleAccessPage, UserRole
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from roles.schema import RoleDetail, EventRoleResponse, RolePermissionEdit, CreateRoleDetail
from  sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from  sqlalchemy.orm import selectinload
from enums import PermissionDetailEnum,PERMISSION_DETAIL_SCHEMA 
from roles.crud import get_role_by_id
from exception import HTTPNotFound

async def get_member_role_id(db: AsyncSession):
    """"
        extract the id of role member
    """
    stmt = select(Role.id).where(Role.rolename.ilike("member"))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_role_services( db:AsyncSession, roledetail : CreateRoleDetail ):
    """ Services to create Role along with the permission of Role"""
    try:
        new_role = Role(
            rolename = roledetail.rolename.lower(),
            can_edit = roledetail.can_edit,
            can_create = roledetail.can_create,
            can_delete = roledetail.can_delete,
            can_edit_users = roledetail.can_edit_users,
            can_create_users = roledetail.can_create_users,
            can_delete_users = roledetail.can_delete_users,
            can_edit_roles = roledetail.can_edit_roles,
            can_create_roles = roledetail.can_create_roles,
            can_delete_roles = roledetail.can_delete_roles,
            can_edit_events = roledetail.can_edit_events,
            can_create_events = roledetail.can_create_events,
            can_delete_events = roledetail.can_delete_events,
        )
        db.add(new_role)
        await db.flush()
        roleaccess = roledetail.roleaccessdetail
        new_access_page = RoleAccessPage(
            role_id = new_role.id,
            home_page = roleaccess.home_page,
            event_page = roleaccess.event_page,
            user_page = roleaccess.user_page,
            profile_page = roleaccess.profile_page,
            tiesheet_page = roleaccess.tiesheet_page,
            group_page = roleaccess.group_page,
            round_config_page = roleaccess.round_config_page,
            qualifier_page = roleaccess.qualifier_page,
            participants_page = roleaccess.participants_page,
            column_config_page = roleaccess.column_config_page,
            group_stage_standing_page = roleaccess.group_stage_standing_page,
            todays_game_page = roleaccess.todays_game_page,
            role_page = roleaccess.role_page
        )
        db.add(new_access_page)
        await db.commit()
        return{
            "message" : "Role and its permission added successfully"
        }
    except SQLAlchemyError as e:
        await db.rollback()
        return {
            "message" : "Failed to add Role"
        }
    
async def get_role_by_permssion_services(
    db : AsyncSession,
    user_id: UUID,
    event_id: UUID | None = None,
):
    base_stmt = (
        select(UserRole)
        .options(
            selectinload(UserRole.role)
            .selectinload(Role.roleaccesspage)
        )
        .where(UserRole.user_id == user_id)
    )
    roledetail = []

    if event_id:
        stmt = base_stmt.where(UserRole.event_id == event_id)
        result = await db.execute(stmt)
        roledetail = result.scalars().all()

    if not roledetail:
        result = await db.execute(base_stmt)
        roledetail = result.scalars().all()

    if not roledetail:
        return None

    return [EventRoleResponse.model_validate(rd) for rd in roledetail]

async def get_permission_detail_services(
    db : AsyncSession,
    permission_detail : PermissionDetailEnum
):
    stmt =  select(Role).order_by(Role.created_at)

    if permission_detail == PermissionDetailEnum.page:
        stmt = stmt.options(selectinload(Role.roleaccesspage))

    result = await db.execute(stmt)
    role_detail = result.scalars().all()

    permission_schema = PERMISSION_DETAIL_SCHEMA[permission_detail.value]

    return [permission_schema.model_validate(rd) for rd in role_detail]

async def edit_role_and_permission_services(
    db : AsyncSession,
    permission_detail : RolePermissionEdit,
    role_id : UUID
):
    role = await get_role_by_id(db = db, role_id=role_id)

    if not role:
        raise HTTPNotFound("Role not found")

    for field, value in permission_detail.dict(exclude={"roleaccessdetail"}).items():
        setattr(role, field, value)

    if not role.roleaccesspage:
        raise HTTPNotFound("Role access page not found")
    
    for field, value in permission_detail.roleaccessdetail.dict().items():
        setattr(role.roleaccesspage, field, value)

    await db.commit()
    await db.refresh(role)

    return {
        "message" : "Role Edited successfully"
    }
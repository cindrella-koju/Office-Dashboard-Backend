from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from roles.schema import RolePermission, RoleResponse, EventRole, EventRoleResponse, RoleDetail, EventDetail, UserDetail, WithinEventDetail, PageDetail, RolePermissionEdit
from models import Role, RoleAccessPage, UserRole
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_, Enum
import enum
from sqlalchemy.orm import selectinload
from uuid import UUID

router = APIRouter()

@router.post("")
async def create_role_with_permission( db: Annotated[AsyncSession, Depends(get_db_session)], roledetail : RolePermission):
    try:
        new_role = Role(
            rolename = roledetail.rolename,
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
            can_manage_events = roledetail.can_manage_events
        )
        db.add(new_role)
        await db.flush()

        new_access_page = RoleAccessPage(
            role_id = new_role.id,
            home_page = roledetail.home_page,
            event_page = roledetail.event_page,
            user_page = roledetail.user_page,
            profile_page = roledetail.profile_page,
            tiesheet_page = roledetail.tiesheet_page,
            group_page = roledetail.group_page,
            round_config_page = roledetail.round_config_page,
            qualifier_page = roledetail.qualifier_page,
            participants_page = roledetail.participants_page,
            column_config_page = roledetail.column_config_page,
            group_stage_standing_page = roledetail.group_stage_standing_page,
            todays_game_page = roledetail.todays_game_page,
            role_page = roledetail.role_page

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

@router.get("")
async def get_roles_with_permissions(db: Annotated[AsyncSession, Depends(get_db_session)], role_id : UUID | None = None):
    stmt = select(Role).options(selectinload(Role.roleaccesspage)).order_by(Role.created_at)

    if role_id:
        stmt = stmt.where(Role.id == role_id)

    result = await db.execute(stmt)
    roles = result.scalars().all()
    
    return [RoleResponse.model_validate(role) for role in roles]
    

@router.post("/event")
async def create_user_role_in_event_with_permission(db: Annotated[AsyncSession, Depends(get_db_session)],user_role_detail : EventRole):

    new_user_role = UserRole(
        user_id = user_role_detail.user_id,
        event_id = user_role_detail.event_id,
        role_id = user_role_detail.role_id
    )
    db.add(new_user_role)
    await db.commit()

    return {
        "message" : "User Permission added successfully"
    }

@router.get("/user/{user_id}/event/{event_id}")
async def get_role_by_permission(db: Annotated[AsyncSession, Depends(get_db_session)], user_id : UUID,event_id : UUID):
    stmt  = select(UserRole).options(selectinload(UserRole.role).selectinload(Role.roleaccesspage)).where(
        and_(
            UserRole.user_id == user_id,
            UserRole.event_id == event_id
        )
    )
    result = await db.execute(stmt)
    roledetail = result.scalars().all()

    reponse = [EventRoleResponse.model_validate(rd) for rd in roledetail]
    # return roledetail
    return reponse[0].role

class PermissionDetailEnum(enum.Enum):
    role = "role"
    event = "event"
    user = "user"
    within_event = "within_event"
    page = "page"

PERMISSION_DETAIL_SCHEMA = {
    "role" : RoleDetail,
    "event" : EventDetail,
    "user" : UserDetail,
    "within_event" : WithinEventDetail,
    "page" : PageDetail
}

@router.get("/detail")
async def get_permission_detail(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    permission_detail : PermissionDetailEnum
):
    stmt =  select(Role)

    if permission_detail == PermissionDetailEnum.page:
        stmt = stmt.options(selectinload(Role.roleaccesspage))

    result = await db.execute(stmt)
    role_detail = result.scalars().all()

    permission_schema = PERMISSION_DETAIL_SCHEMA[permission_detail.value]

    return [permission_schema.model_validate(rd) for rd in role_detail]

    
@router.put("/{role_id}")
async def edit_role_and_permission(db: Annotated[AsyncSession, Depends(get_db_session)], permission_detail:RolePermissionEdit,role_id : UUID):
    stmt = select(Role).options(selectinload(Role.roleaccesspage)).where(Role.id == role_id)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    for field, value in permission_detail.dict(exclude={"roleaccessdetail"}).items():
        setattr(role, field, value)

    # Page access flags
    if not role.roleaccesspage:
        raise HTTPException(status_code=400, detail="Role access page not found")

    for field, value in permission_detail.roleaccessdetail.dict().items():
        setattr(role.roleaccesspage, field, value)

    await db.commit()
    await db.refresh(role)

    return {
        "message" : "Role Edited successfully"
    }
    # return [RolePermissionEdit.model_validate(rp) for rp in role_permission]
# Role id: 98fb6eb2-ccf9-4df6-98a3-4fcb291e8a3b
# User id: ae347041-c28c-43ea-aee2-16b7ebecc7b0
# Event id : 9416e4bc-c260-45c4-a5ed-d453b58c1bf6
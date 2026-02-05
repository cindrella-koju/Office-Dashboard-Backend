from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from roles.schema import RolePermission, RoleResponse, EventRole, EventRoleResponse, RoleDetail, EventDetail, UserDetail, WithinEventDetail, PageDetail
from models import Role, RoleAccessPage, UserRole
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_
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

@router.get("/detail")
async def get_permission_detail(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    role : bool | None = None, 
    event: bool| None = None,
    user : bool | None = None,
    within_event : bool | None = None,
    page_detail : bool | None = None
):
    stmt =  select(Role)

    if page_detail:
        stmt = stmt.options(selectinload(Role.roleaccesspage))

    result = await db.execute(stmt)
    role_detail = result.scalars().all()

    if role:
        return [RoleDetail.model_validate(rd) for rd in role_detail]
    
    if event:
        return [EventDetail.model_validate(rd) for rd in role_detail]
    
    if user:
        return [UserDetail.model_validate(rd) for rd in role_detail]
    
    if within_event:
        return [WithinEventDetail.model_validate(rd) for rd in role_detail]
    
    if page_detail:
        return role_detail
    

# Role id: 98fb6eb2-ccf9-4df6-98a3-4fcb291e8a3b
# User id: ae347041-c28c-43ea-aee2-16b7ebecc7b0
# Event id : 9416e4bc-c260-45c4-a5ed-d453b58c1bf6
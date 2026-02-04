from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from roles.schema import RolePermission, RoleResponse
from models import Role, RoleAccessPage
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

router = APIRouter()

@router.post("")
async def create_role_with_permission( db: Annotated[AsyncSession, Depends(get_db_session)], roledetail : RolePermission):
    try:
        new_role = Role(
            rolename = roledetail.rolename,
            can_view = roledetail.can_view,
            can_edit = roledetail.can_edit,
            can_create = roledetail.can_create,
            can_delete = roledetail.can_delete,
            can_view_users = roledetail.can_view_users,
            can_edit_users = roledetail.can_edit_users,
            can_create_users = roledetail.can_create_users,
            can_delete_users = roledetail.can_delete_users,
            can_view_roles = roledetail.can_view_roles,
            can_edit_roles = roledetail.can_edit_roles,
            can_create_roles = roledetail.can_create_roles,
            can_delete_roles = roledetail.can_delete_roles,
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
    
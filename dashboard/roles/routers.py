from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from roles.schema import RoleResponse, EventRole,RolePermissionEdit, CreateRoleDetail
from models import Role, UserRole
from sqlalchemy import select,delete
from enums import PermissionDetailEnum
from sqlalchemy.orm import selectinload
from uuid import UUID
from exception import HTTPNotFound
from roles.crud import get_role_by_id
from roles.services import create_role_services, get_role_by_permssion_services, get_permission_detail_services, edit_role_and_permission_services
router = APIRouter()

@router.post("")
async def create_role_with_permission( db: Annotated[AsyncSession, Depends(get_db_session)], roledetail : CreateRoleDetail):
    return await create_role_services( db=db, roledetail=roledetail)

@router.get("")
async def get_roles_with_permissions(db: Annotated[AsyncSession, Depends(get_db_session)], role_id : UUID | None = None):
    stmt = select(Role).options(selectinload(Role.roleaccesspage)).order_by(Role.created_at)

    if role_id:
        stmt = stmt.where(Role.id == role_id)

    result = await db.execute(stmt)
    roles = result.scalars().all()
    
    return [RoleResponse.model_validate(role) for role in roles]
    

@router.get("/all")
async def get_all_role(db: Annotated[AsyncSession, Depends(get_db_session)]):
    stmt = select(Role.id, Role.rolename.label("name"))
    result = await db.execute(stmt)
    return result.mappings().all()

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

@router.get("/user/{user_id}/event")
async def get_role_by_permission(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID,
    event_id: UUID | None = None,
):
    """ Extract user permission based on role """
    response = await get_role_by_permssion_services(db = db, user_id=user_id, event_id=event_id)
    return response[0].role

@router.get("/detail")
async def get_permission_detail(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    permission_detail : PermissionDetailEnum
):
    """Get the permission detail based on user, event , pages .... """
    return await get_permission_detail_services( db=db, permission_detail=permission_detail)

    
@router.put("/{role_id}")
async def edit_role_and_permission(db: Annotated[AsyncSession, Depends(get_db_session)], permission_detail:RolePermissionEdit,role_id : UUID):
    return await edit_role_and_permission_services( db=db, permission_detail=permission_detail, role_id=role_id)


@router.get("/filter")
async def get_role_for_filter(db: Annotated[AsyncSession, Depends(get_db_session)],not_in_event: bool = False):
    stmt = select(Role.id, Role.rolename.label("name"))

    if not_in_event:
        stmt = stmt.join(UserRole, UserRole.role_id == Role.id).where(UserRole.event_id.is_(None))

    stmt = stmt.distinct()

    result = await db.execute(stmt)

    roles = [dict(row) for row in result.mappings().all()]

    return roles

@router.delete("/{role_id}")
async def delete_role_and_permission(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    role_id : UUID
):
    role = await get_role_by_id(db = db, role_id=role_id)

    if not role:
        raise HTTPNotFound("Role not found")
    
    stmt = delete(Role).where(Role.id == role_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Role {role.rolename} deleted successfully"
    }

@router.get("/event/{event_id}")
async def extract_event_role(db: Annotated[AsyncSession, Depends(get_db_session)],event_id : UUID):
    stmt = select(UserRole.role_id.label("id"),Role.rolename.label("name")).join(Role, Role.id == UserRole.role_id).where(UserRole.event_id == event_id).distinct()
    result = await db.execute(stmt)
    return result.mappings().all()
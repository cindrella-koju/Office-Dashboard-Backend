from fastapi import APIRouter, Depends
from db_connect import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from events.eventrole.schema import createEventRole, EditEventRole
from events.eventrole.services import EventRoleServices
from uuid import UUID

router = APIRouter()

@router.post("/{event_id}")
async def create_event_role(db : Annotated[AsyncSession,Depends(get_db_session)], eventrole : createEventRole, event_id : UUID):
    return await EventRoleServices.create_event_role(db=db, eventrole=eventrole, event_id=event_id)

@router.get("/{event_id}")
async def get_event_role(db: Annotated[AsyncSession,Depends(get_db_session)], event_id : UUID):
    return await EventRoleServices.get_event_role(db=db, event_id = event_id)

@router.put("/{event_role_id}")
async def edit_event_role(db : Annotated[AsyncSession,Depends(get_db_session)], event_role_id : UUID, editeventrole : EditEventRole):
    return await EventRoleServices.edit_event_role(db=db, event_role_id=event_role_id, editeventrole=editeventrole)

@router.delete("/{event_role_id}")
async def delete_event_role(db : Annotated[AsyncSession,Depends(get_db_session)], event_role_id : UUID):
    return await EventRoleServices.delete_event_role(db=db, event_role_id=event_role_id)
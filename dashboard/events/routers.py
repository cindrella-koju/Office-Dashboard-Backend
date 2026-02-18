from events.schema import EventDetail, StatusEnum, EventDetailResponse, EditEventDetail
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from models import Event
from dependencies import get_current_user
from uuid import UUID
from events.services import extract_all_event, create_event_services, edit_event_services
from sqlalchemy import select, delete
from events.crud import extract_event_by_id
from exception import HTTPNotFound
from events.stage.routers import router as state_router
from events.group.routers import router as group_router
from events.standingcolumn.routers import router as column_router
from events.tiesheet.routers import router as tiesheet_router
from events.qualifier.routers import router as qualifier_router
from events.overalltiesheet.routers import router as overalltiesheet_router
from events.match.routers import router as match_router

router = APIRouter()
router.include_router(state_router,prefix="/stage",tags=["Stage"])
router.include_router(group_router,prefix="/group",tags=["Group"])
router.include_router(column_router,prefix="/column",tags=["Column"])
router.include_router(tiesheet_router, prefix="/tiesheet",tags=["Tiesheet"])
router.include_router(qualifier_router, prefix="/qualifier",tags=["Qualifier"])
router.include_router(overalltiesheet_router,prefix="/overalltiesheet",tags=["Overalltiesheet"])
router.include_router(match_router,prefix="/match", tags=["Match"])

@router.post("")
async def create_event( 
    event : EventDetail, 
    db : Annotated[AsyncSession,Depends(get_db_session)],
    # current_user: dict = Depends(get_current_user),
):
    return await create_event_services(db=db, event=event)

@router.get("")
async def retrieve_event(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status : str | None = None
):
    return await extract_all_event(db=db, status=status)
    
@router.patch("")
async def edit_event(
    event_detail : EditEventDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID,
    # current_user: dict = Depends(get_current_user),
):
    return await edit_event_services(db=db, event_detail=event_detail, event_id=event_id)
    

@router.delete("/{event_id}")
async def delete_event(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID ,
    # current_user: dict = Depends(get_current_user),
):    
    event = await extract_event_by_id( db=db, event_id=event_id)

    if not event:
        raise HTTPNotFound("Event not found")
    
    stmt = delete(Event).where(Event.id == event_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Event {event.title} deleted successfully"
    }

from events.schema import EventDetail, StatusEnum, EventDetailResponse, EditEventDetail
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from models import Event
from dependencies import get_current_user
from uuid import UUID
from events.services import extract_all_event, create_event_services, extract_one_event
from sqlalchemy import select, delete
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
    # if current_user["role"] == RoleEnum.superadmin and current_user["role"] == RoleEnum.admin
    result = await create_event_services(db=db, event=event)
    return result


@router.get("")
async def retrieve_event(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status : str | None = None
):
    events = await extract_all_event(db=db, status=status)
    if not events:
        return{
            "detail":"Event not found",
        }
    return [EventDetailResponse.model_validate(event) for event in events]
    
@router.patch("")
async def edit_user(
    event_detail : EditEventDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID,
    # current_user: dict = Depends(get_current_user),
):
    event = await extract_one_event(db=db, event_id=event_id)
    if not event:
        raise HTTPException(
            detail="Event not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if event_detail.title:
        event.title = event_detail.title

    if event_detail.description:
        event.description = event_detail.description

    if event_detail.startdate:
        event.startdate = event_detail.startdate

    if event_detail.enddate:
        event.enddate = event_detail.enddate

    if event_detail.status:
        event.status = StatusEnum(event_detail.status)

    if event_detail.progress_note:
        event.progress_note = event_detail.progress_note

    await db.commit()

    return{
        "message" : "Event Updated Successfully",
        "event_id" :  event_id
    }



@router.delete("/{event_id}")
async def delete_event(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID ,
    # current_user: dict = Depends(get_current_user),
):    
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()

    if not event:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found"
                )
    
    stmt = delete(Event).where(Event.id == event_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"User {event.title} deleted successfully"
    }

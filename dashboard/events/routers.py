from events.schema import EventDetail, StatusEnum, EventDetailResponse, EditEventDetail
from users.schema import RoleEnum
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from models import Event
from dependencies import get_current_user
from uuid import UUID
from events.services import extract_all_event, extract_one_event
from sqlalchemy import select, delete

router = APIRouter()

@router.post("")
async def create_event( 
    event : EventDetail, 
    db : Annotated[AsyncSession,Depends(get_db_session)],
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] == RoleEnum.superadmin and current_user["role"] == RoleEnum.admin:
        event_description, event_progress_note = "", ""
        if event.description:
            event_description = event.description

        if event.progress_note:
            event_progress_note = event.progress_note

        new_event = Event(
            title = event.title,
            description = event_description,
            startdate = event.startdate,
            enddate = event.enddate,
            status = StatusEnum(event.status),
            progress_note = event_progress_note
        )

        db.add(new_event)
        await db.commit()
        return{
            "message" : "Event Added successfully",
            "id" : new_event.id
        }
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

@router.get("")
async def retrieve_event(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID | None = None,
):
    if event_id:
        event = await extract_one_event(db=db, event_id=event_id)
        if not event:
            raise HTTPException(
                detail="Event not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return EventDetailResponse(**event.__dict__)
    else:
        events = await extract_all_event(db=db)
        if not events:
            raise HTTPException(
                detail="Event not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return [EventDetailResponse(**event.__dict__) for event in events]
    
@router.patch("")
async def edit_user(
    event_detail : EditEventDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID | None = None,
    current_user: dict = Depends(get_current_user),
):
    print("Role:",RoleEnum(current_user["role"]))
    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="event_id required")
    
    if current_user["role"] != RoleEnum.superadmin and current_user["role"] != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
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



@router.delete("")
async def delete_event(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID | None = None,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != RoleEnum.superadmin and current_user["role"] != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="event_id required")
    
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
        "message" : f"User {event_id} deleted successfully"
    }

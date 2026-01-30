from events.schema import EventDetail, StatusEnum, EventDetailResponse, EditEventDetail
from users.schema import RoleEnum
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from models import Event, Stage, StandingColumn
from dependencies import get_current_user
from uuid import UUID
from events.services import extract_all_event, extract_one_event
from sqlalchemy import select, delete
from events.stage.routers import router as state_router
from events.group.routers import router as group_router
from events.standingcolumn.routers import router as column_router
from events.tiesheet.routers import router as tiesheet_router
from events.qualifier.routers import router as qualifier_router
from events.overalltiesheet.routers import router as overalltiesheet_router
from events.match.routers import router as match_router
from sqlalchemy.exc import SQLAlchemyError

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
    try:
        new_event = Event(
            title=event.title,
            description=event.description or "",
            startdate=event.startdate,
            enddate=event.enddate,
            status=StatusEnum(event.status),
            progress_note=event.progress_note or "",
        )

        db.add(new_event)
        await db.flush()  # ensures new_event.id exists

        new_round = Stage(
            event_id=new_event.id,
            name="Round 1",
            round_order=1
        )
        db.add(new_round)
        await db.flush()  # ensures new_round.id exists

        default_standing_col = [
            {"column_field": "Match Played", "default_value": "0"},
            {"column_field": "Win", "default_value": "0"},
            {"column_field": "Loss", "default_value": "0"},
            {"column_field": "Draw", "default_value": "0"},
            {"column_field": "Points", "default_value": "0"},
        ]

        new_standing_columns = [
            StandingColumn(
                stage_id=new_round.id,
                column_field=col["column_field"],
                default_value=col["default_value"]
            )
            for col in default_standing_col
        ]

        db.add_all(new_standing_columns)
        await db.commit()

        return {
            "message": "Event added successfully",
            "id": new_event.id
        }
    except SQLAlchemyError as e:
        await db.rollback()
        return {
            "message": "Failed to add Event",
            "error": str(e)
        }
    # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

@router.get("")
async def retrieve_event(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID | None = None,
):
    if event_id:
        event = await extract_one_event(db=db, event_id=event_id)
        if not event:
            return{
                "detail":"Event not found",
            }
        return EventDetailResponse.model_validate(event)
    else:
        events = await extract_all_event(db=db)
        if not events:
            return{
                "detail":"Event not found",
            }
        return [EventDetailResponse.model_validate(event) for event in events]
    
@router.patch("")
async def edit_user(
    event_detail : EditEventDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID | None = None,
    # current_user: dict = Depends(get_current_user),
):
    # print("Role:",RoleEnum(current_user["role"]))
    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="event_id required")
    
    # if current_user["role"] != RoleEnum.superadmin and current_user["role"] != RoleEnum.admin:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
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


# async def test_get_events():
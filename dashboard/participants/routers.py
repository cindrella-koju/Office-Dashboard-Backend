from models import user_event_association, User, Event
from fastapi import APIRouter, Depends, HTTPException, status
from participants.schema import Participants, ParticipantsUserResponse, ParticipantsEventResponse
from db_connect import get_db_session
from dependencies import get_current_user
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from users.schema import RoleEnum
from sqlalchemy import insert, select
from uuid import UUID

router = APIRouter()

@router.post("")
async def create_participants(
    participant : Participants, 
    db: Annotated[AsyncSession, Depends(get_db_session)],
    # current_user: dict = Depends(get_current_user)
):
    # if current_user["role"] != RoleEnum.superadmin and current_user["role"] != RoleEnum.admin:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    stmt = insert(user_event_association).values(
        user_id=participant.user_id,
        event_id=participant.event_id,
        is_winner=False,
    )

    await db.execute(stmt)
    await db.commit()

    return {"message": "Participant added successfully"}

@router.get("/event")
async def extract_participant_by_event(
    event_id : UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != RoleEnum.superadmin and current_user["role"] != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    stmt = (
        select(
            user_event_association.c.user_id,
            user_event_association.c.event_id,
            user_event_association.c.is_winner,
            User.username,
        )
        .join(User, User.id == user_event_association.c.user_id)
        .where(user_event_association.c.event_id == event_id)
    )

    result = await db.execute(stmt)
    participants = result.mappings().all()

    return [ParticipantsEventResponse(**p) for p in participants]

@router.get("/user")
async def extract_participant_by_event(
    user_id : UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != RoleEnum.superadmin and current_user["role"] != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    stmt = (
        select(
            user_event_association.c.user_id,
            user_event_association.c.event_id,
            user_event_association.c.is_winner,
            User.username,
            Event.title
        )
        .join(User, User.id == user_event_association.c.user_id)
        .join(Event, Event.id == user_event_association.c.event_id)
        .where(user_event_association.c.event_id == user_id)
    )

    result = await db.execute(stmt)
    participants = result.mappings().all()

    return [ParticipantsUserResponse(**p) for p in participants]

    
# from sqlalchemy import select

# stmt = select(user_event_association).where(
#     user_event_association.c.event_id == event.id,
#     user_event_association.c.is_winner == True
# )

# winners = session.execute(stmt).all()

from models import user_event_association, User, Qualifier
from fastapi import APIRouter, Depends
from participants.schema import Participants, Participants, UserParticipantOrNot
from db_connect import get_db_session
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,and_
from uuid import UUID
from participants.services import ParticipantsServices
from participants.crud import extract_participants

router = APIRouter()

@router.post("")
async def create_participants(
    event_id: UUID,
    participants: Participants,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    return await ParticipantsServices.create_participants(db=db, event_id=event_id, participants=participants)



@router.get("/event")
async def extract_participant_by_event(
    event_id : UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):  
    return await ParticipantsServices.extract_participant_by_event(db=db, event_id=event_id)
      

@router.get("/user")
async def extract_participant_by_event_with_user(
    user_id : UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    return await ParticipantsServices.extract_participant_by_event_with_user(db=db, user_id=user_id)

@router.get("")
async def retrieve_participants(event_id: UUID, db: Annotated[AsyncSession,Depends(get_db_session)]):
    participants = await extract_participants(event_id=event_id, db=db)

    return{
        "participants" : participants
    }

@router.get("/not-participants")
async def retrieve_not_participants(event_id : UUID,  db: Annotated[AsyncSession,Depends(get_db_session)]):
    participants = await extract_participants(event_id=event_id, db=db)
    participant_ids = [p.id for p in participants]

    stmt = select(User.id,User.username).where(User.id.notin_(participant_ids))
    result = await db.execute(stmt)  
    users = result.all()
    
    return [ UserParticipantOrNot.model_validate(user) for user in users]

@router.get("/not_qualifier")
async def retrieve_user_not_in_qualifier(stage_id : UUID,event_id : UUID,db: Annotated[AsyncSession,Depends(get_db_session)]):
    stmt = (select(User.id,User.username)
            .join(user_event_association,user_event_association.c.user_id == User.id)
            .outerjoin(
                Qualifier,
                and_(
                    user_event_association.c.user_id == Qualifier.user_id,
                    user_event_association.c.event_id == Qualifier.event_id,
                    Qualifier.stage_id == stage_id
                )
            ).where(and_(Qualifier.id == None,user_event_association.c.event_id == event_id)))
    result = await db.execute(stmt)
    users = result.all()
    return [ UserParticipantOrNot.model_validate(u) for u in users]


@router.get("/not-in-group/event/{event_id}/stage/{stage_id}")
async def participants_not_in_group(event_id : UUID, stage_id:UUID, db: Annotated[AsyncSession,Depends(get_db_session)], group_id : UUID | None = None):
    return await ParticipantsServices.get_participants_not_in_group(
        db = db,
        event_id=event_id,
        stage_id=stage_id,
        group_id=group_id
    )



@router.delete("/{user_id}/event/{event_id}")
async def delete_participants(user_id : UUID, event_id : UUID, db: Annotated[AsyncSession,Depends(get_db_session)]):
    return await ParticipantsServices.delete_participants(db=db, user_id=user_id, event_id=event_id)
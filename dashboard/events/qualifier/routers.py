from models import user_event_association, User, Event, GroupMembers, Event, Stage, Group, StandingColumn, ColumnValues, Qualifier
from fastapi import APIRouter, Depends, HTTPException, status
from participants.schema import Participants, ParticipantsUserResponse, ParticipantsEventResponse, UserResponse
from db_connect import get_db_session
from dependencies import get_current_user
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from users.schema import RoleEnum
from sqlalchemy import insert, select
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

class QualifierModel(BaseModel):
    user_id : list[UUID]

router = APIRouter()

@router.get("")
async def retrieve_qualifier_by_round(stage_id : UUID,  db: Annotated[AsyncSession, Depends(get_db_session)]):
    stmt = select(Qualifier.user_id, User.username).join(User,User.id == Qualifier.user_id).where(Qualifier.stage_id == stage_id )
    result = await db.execute(stmt)
    users = result.all()

    return [
        {
            "id" :  user.user_id,
            "username" : user.username
        }

        for user in users
    ]

@router.post("")
async def create_qualifier(event_id : UUID,stage_id:UUID,db: Annotated[AsyncSession, Depends(get_db_session)], qualifier : QualifierModel):
    new_qualifier = [Qualifier(
            event_id = event_id,
            user_id = q,
            stage_id = stage_id
        )
        for q in qualifier.user_id
    ]

    db.add_all(new_qualifier)
    await db.commit()

    return{
        "message" : "Qualifier created Succeddfully"
    }

@router.get("/event")
async def retrieve_qualifiers_by_event(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    stmt = (
        select(
            User.id.label("user_id"),
            User.username,
            Stage.name.label("round_name"),
        )
        .select_from(Qualifier)
        .join(User, User.id == Qualifier.user_id)
        .join(Stage, Stage.id == Qualifier.stage_id)
        .where(Qualifier.event_id == event_id)
    )

    result = await db.execute(stmt)
    return result.mappings().all()
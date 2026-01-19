from models import user_event_association, User, Event, GroupMembers, Event, Stage, Group, StandingColumn, ColumnValues, Qualifier
from fastapi import APIRouter, Depends, HTTPException, status
from participants.schema import Participants, ParticipantsUserResponse, ParticipantsEventResponse, UserResponse
from db_connect import get_db_session
from dependencies import get_current_user
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from users.schema import RoleEnum
from sqlalchemy import insert, select, exists
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
router = APIRouter()

@router.get("")
async def retrieve_qualifier_by_round(stage_id : UUID,  db: Annotated[AsyncSession, Depends(get_db_session)],):
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
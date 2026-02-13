from models import user_event_association, User, Event, GroupMembers, Event, Stage, Group, StandingColumn, ColumnValues, Qualifier
from fastapi import APIRouter, Depends, HTTPException, status
from participants.schema import Participants, ParticipantsUserResponse, ParticipantsEventResponse, UserResponse
from db_connect import get_db_session
from dependencies import get_current_user
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from users.schema import RoleEnum
from sqlalchemy import insert, select, delete
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from events.qualifier.services import QualifierService

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
async def create_qualifier(
    event_id: UUID,
    stage_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    qualifier: QualifierModel
):
    try:
        # 1. Create new Qualifiers for each user
        new_qualifiers = [
            Qualifier(
                event_id=event_id,
                user_id=user_id,
                stage_id=stage_id
            )
            for user_id in qualifier.user_id
        ]

        db.add_all(new_qualifiers)
        await db.commit()

        # 2. Fetch the columns and their default values for the given stage
        result = await db.execute(
            select(
                StandingColumn.id,
                StandingColumn.default_value
            ).where(StandingColumn.stage_id == stage_id)
        )
        cols_and_vals = result.all()

        # 3. Create ColumnValues for each user & column
        new_column_values = [
            ColumnValues(
                user_id=user_id,
                column_id=col_id,
                value=default_value
            )
            for user_id in qualifier.user_id
            for col_id, default_value in cols_and_vals
        ]

        db.add_all(new_column_values)
        await db.commit()

        return {"message": "Qualifier created successfully"}

    except Exception as e:
        # Rollback in case of any error
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/event")
async def retrieve_qualifiers_by_event(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    stmt = (
        select(
            Qualifier.id.label("qualifier_id"),
            User.id.label("user_id"),
            User.email,
            User.username,
            Stage.name.label("round_name"),
        )
        .select_from(Qualifier)
        .join(User, User.id == Qualifier.user_id)
        .join(Stage, Stage.id == Qualifier.stage_id)
        .where(Qualifier.event_id == event_id)
    )

    result = await db.execute(stmt)
    info = result.mappings().all()

    # Group the results by round_name
    grouped = {}
    for row in info:
        round_name = row["round_name"]
        user_data = {
            "qualifier_id" : row["qualifier_id"],
            "user_id": row["user_id"],
            "username": row["username"],
            "email" : row["email"]
        }
        if round_name not in grouped:
            grouped[round_name] = {"round_name": round_name, "qualifier": []}
        
        grouped[round_name]["qualifier"].append(user_data)

    return list(grouped.values())

@router.delete("/{qualifier_id}")
async def delete_qualifier(
    qualifier_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    qualifier =  await QualifierService.extract_username_from_qualifier_id(db = db, qualifier_id=qualifier_id)
    stmt = delete(Qualifier).where(Qualifier.id == qualifier_id)
    await db.execute(stmt)
    await db.commit()

    return{
        "message" : f"Qualifier {qualifier} deleted successfully"
    }
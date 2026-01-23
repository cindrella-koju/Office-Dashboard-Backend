from fastapi import APIRouter, Depends
from uuid import UUID
from typing import Optional, List
from sqlalchemy import select, and_
from models import StandingColumn, ColumnValues, Qualifier, User, Stage
from db_connect import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from events.overalltiesheet.schema import Round

router = APIRouter()

@router.get("")
async def retrieve_overall_points_by_round_and_event(event_id : UUID,db : Annotated[AsyncSession,Depends(get_db_session)],stage_id:Optional[UUID] = None):
    if stage_id:
        stmt = (
            select(User.id.label("id"), User.username.label("username"),Stage.name,StandingColumn.column_field,ColumnValues.value)
            .join(Qualifier, Qualifier.user_id == User.id)
            .join(Stage, Stage.id == Qualifier.stage_id)
            .join(StandingColumn,StandingColumn.stage_id == Stage.id)
            .join(
                ColumnValues,
                and_(
                    ColumnValues.column_id == StandingColumn.id,
                    ColumnValues.user_id == User.id
                )
            )
            .where(
                and_(
                    Qualifier.event_id == event_id,
                    Qualifier.stage_id == stage_id
                )
            )
        )
    else:
        stmt = (
            select(User.id.label("id"), User.username.label("username"),Stage.name,StandingColumn.column_field,ColumnValues.value)
            .join(Qualifier, Qualifier.user_id == User.id)
            .join(Stage, Stage.id == Qualifier.stage_id)
            .join(StandingColumn,StandingColumn.stage_id == Stage.id)
            .join(
                ColumnValues,
                and_(
                    ColumnValues.column_id == StandingColumn.id,
                    ColumnValues.user_id == User.id
                )
            )
            .where(
                and_(
                    Qualifier.event_id == event_id,
                )
            )
        )

    # stmt = select(StandingColumn.column_field).where(StandingColumn.stage_id == stage_id)
    result = await db.execute(stmt)
    users = result.mappings().all()


    dict_form = {}

    for user in users:
        col_value = {
            "column_name": user.column_field,
            "column_value": user.value
        }

        if user.name not in dict_form:
            dict_form[user.name] = {
                "round_name": user.name,
                "users": [
                    {
                        "user_id": user.id,
                        "username": user.username,
                        "column_detail": [col_value] 
                    }
                ]
            }
        else:
            # Check if user Already exist
            existing_user = None

            for u in dict_form[user.name]["users"]:
                if u["user_id"] == user.id:
                    existing_user = u

            # If exist append the detail in column_detail
            if existing_user:
                existing_user["column_detail"].append(col_value)
            else:
                # Not exist then add new user in round
                dict_form[user.name]["users"].append({
                    "user_id": user.id,
                    "username": user.username,
                    "column_detail": [col_value]
                })

    rounds: List[Round] = [Round(**round_data) for round_data in dict_form.values()]
    return rounds
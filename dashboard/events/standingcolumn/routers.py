from fastapi import APIRouter, Depends
from models import StandingColumn, ColumnValues
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session
from events.standingcolumn.schema import CreateColumn, EditColumn, CreateValues, ColumnResponse
from events.standingcolumn.sevices import StandingColumnServices
from events.standingcolumn.crud import extract_column_by_id

router = APIRouter()

@router.post("")
async def create_column(
    columnDetail: CreateColumn, 
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
   return await StandingColumnServices.create_column(db=db, columnDetail=columnDetail)

@router.patch("/{column_id}")
async def edit_column(column_id : UUID,columnDetail : EditColumn, db : Annotated[AsyncSession,Depends(get_db_session)]):
    return await StandingColumnServices.edit_column(db=db, column_id=column_id, columnDetail=columnDetail)

@router.get("")
async def retrieve_column(db : Annotated[AsyncSession,Depends(get_db_session)],stage_id : UUID):
    result = await db.execute(select(StandingColumn).where(StandingColumn.stage_id == stage_id))
    stages = result.scalars().all()
    return [ColumnResponse.model_validate(stage) for stage in stages]

@router.delete("/{column_id}")
async def delete_column(column_id : UUID,db : Annotated[AsyncSession,Depends(get_db_session)]):
    column = await extract_column_by_id(db=db, column_id=column_id)

    stmt = delete(StandingColumn).where(StandingColumn.id == column_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Column {column.column_field} deleted successfully"
    }

@router.post("/values")
async def create_value(value_detail : CreateValues, db : Annotated[AsyncSession,Depends(get_db_session)]):
    new_value = ColumnValues(
        user_id = value_detail.user_id,
        column_id = value_detail.column_id,
        value = value_detail.value
    )

    db.add(new_value)
    await db.commit()
    return{
        "message" : "Value added successfully"
    }
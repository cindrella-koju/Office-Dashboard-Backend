from fastapi import APIRouter, Depends, HTTPException, status
from models import StandingColumn, ColumnValues, Qualifier
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session
from events.standingcolumn.schema import CreateColumn, EditColumn, CreateValues, ColumnResponse
# from 
router = APIRouter()

@router.post("")
async def create_column(
    columnDetail: CreateColumn, 
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    try:
        new_column = StandingColumn(
            stage_id=columnDetail.stage_id,
            column_field=columnDetail.column_field,
            default_value=columnDetail.default_value,
        )

        db.add(new_column)
        await db.flush()

        # Get all users for this stage
        stmt = select(Qualifier.user_id).where(Qualifier.stage_id == columnDetail.stage_id)
        result = await db.execute(stmt)
        users = result.scalars().all()

        # Create default column values for each user
        if users:
            user_standing_col = [
                ColumnValues(
                    user_id=user_id,
                    column_id=new_column.id,
                    value=columnDetail.default_value
                )
                for user_id in users
            ]
            db.add_all(user_standing_col)

        await db.commit()

        return {
            "message": "Column Added successfully",
            "id": new_column.id
        }
    except SQLAlchemyError as e:
        await db.rollback()
        return {
            "message": "Failed to create Column",
            "error": str(e)
        }

@router.patch("/{column_id}")
async def edit_column(column_id : UUID,columnDetail : EditColumn, db : Annotated[AsyncSession,Depends(get_db_session)]):
    result = await db.execute(select(StandingColumn).where(StandingColumn.id == column_id))
    column = result.scalars().first()

    if not column:
        raise HTTPException(
            detail="Column not found",
            status_code= status.HTTP_404_NOT_FOUND
        )
    
    if columnDetail.stage_id:
        column.stage_id = columnDetail.stage_id

    if columnDetail.column_field:
        column.column_field = columnDetail.column_field



    await db.commit()

    return {
        "message" : "Stage Update Successfully",
        "stage_id" : column_id
    }

@router.get("")
async def retrieve_column(db : Annotated[AsyncSession,Depends(get_db_session)],stage_id : UUID):
    # try:
    result = await db.execute(select(StandingColumn).where(StandingColumn.stage_id == stage_id))
    stages = result.scalars().all()
    # if not stages:
    #     raise HTTPException(
    #         detail="Stage not found",
    #         status_code=status.HTTP_404_NOT_FOUND
    #     )
    return [ColumnResponse.model_validate(stage) for stage in stages]
# except SW;

@router.delete("/{column_id}")
async def delete_column(column_id : UUID,db : Annotated[AsyncSession,Depends(get_db_session)]):
    result = await db.execute(select(StandingColumn).where(StandingColumn.id == column_id))
    column = result.scalars().first()
    if not column:
        raise HTTPException(
            detail="Stage not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

    stmt = delete(StandingColumn).where(StandingColumn.id == column_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Column {column_id} deleted successfully"
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
        "message" : "Value added successfully",
        "id" : new_value.id
    }
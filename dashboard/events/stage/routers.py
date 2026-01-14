from fastapi import APIRouter, Depends, HTTPException, status
from events.stage.schema import StageDetail, EditStageDetail, StageResponse
from models import Stage
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session

router = APIRouter()

@router.post("")
async def create_stage(stage : StageDetail,  db : Annotated[AsyncSession,Depends(get_db_session)]):
    new_state = Stage(
        event_id = stage.event_id,
        name = stage.name,
        round_order = stage.round_order
    )

    db.add(new_state)
    await db.commit()
    return{
        "message" : "Stage added successfully",
        "id" : new_state.id
    }

@router.patch("")
async def edit_stage(
    stage_detail: EditStageDetail,
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID | None = None,
):
    result = await db.execute(select(Stage).where(Stage.id == stage_id))
    stage = result.scalars().first()

    if not stage:
        raise HTTPException(
            detail="Stage not found",
            status_code= status.HTTP_404_NOT_FOUND
        )
    
    if stage_detail.name:
        stage.name = stage_detail.name

    if stage_detail.round_order:
        stage.round_order = stage_detail.round_order

    await db.commit()

    return {
        "message" : "Stage Aded Successfully",
        "stage_id" : stage_id
    }

@router.get("")
async def retrieve_stage(
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID | None = None,
):
    if stage_id:
        result = await db.execute(select(Stage).where(Stage.id == stage_id))
        stage = result.scalars().first()
        if not stage:
            raise HTTPException(
                detail="Stage not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return StageResponse(**stage.__dict__)
    else:
        result = await db.execute(select(Stage))
        stages = result.scalars().all()
        if not stages:
            raise HTTPException(
                detail="Stage not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return [StageResponse(**stage.__dict__) for stage in stages]
    
@router.delete("")
async def delete_stage(
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID | None = None,
):
    result = await db.execute(select(Stage).where(Stage.id == stage_id))
    stage = result.scalars().first()
    if not stage:
        raise HTTPException(
            detail="Stage not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    stmt = delete(Stage).where(Stage.id == stage_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Stage {stage_id} deleted successfully"
    }

    
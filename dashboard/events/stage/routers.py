from fastapi import APIRouter, Depends
from events.stage.schema import RoundInfo, StageDetail, EditStageDetail
from models import Stage
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session
from events.stage.services import StageServices
from events.stage.crud import extract_stage_by_id

router = APIRouter()

@router.post("")
async def create_stage(event_id : UUID,stage : StageDetail,  db : Annotated[AsyncSession,Depends(get_db_session)]):
    return await StageServices.create_stage(db = db, stage=stage, event_id=event_id)

@router.patch("/{stage_id}")
async def edit_stage(
    stage_detail: EditStageDetail,
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID
):
    return await StageServices.edit_stage(db=db, stage_detail=stage_detail, stage_id=stage_id)

@router.get("")
async def retrieve_stage(
    event_id : UUID,
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID | None = None,
):
    return await StageServices.retrieve_stage(db=db, event_id=event_id, stage_id=stage_id)
    
@router.delete("/{stage_id}")
async def delete_stage(
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID
):
    stage = await extract_stage_by_id(db=db, stage_id=stage_id)
    
    stmt = delete(Stage).where(Stage.id == stage_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Stage {stage.name} deleted successfully"
    }


@router.get("/rounds")
async def rounds(db: Annotated[AsyncSession,Depends(get_db_session)], event_id : UUID): 
    stmt = select(Stage).where(Stage.event_id == event_id).order_by(Stage.created_at)
    result = await db.execute(stmt)
    stages = result.scalars().all()

    return [RoundInfo.model_validate(stage) for stage in stages]

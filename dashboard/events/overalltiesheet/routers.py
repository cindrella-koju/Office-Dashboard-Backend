from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional
from db_connect import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from events.overalltiesheet.services import OverallTiesheetServices

router = APIRouter()

@router.get("")
async def retrieve_overall_points_by_round_and_event(
    event_id : UUID,
    db : Annotated[AsyncSession,Depends(get_db_session)],
    stage_id:Optional[UUID] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    return await OverallTiesheetServices.retrieve_overall_points_by_round_and_event(
        db=db, 
        event_id=event_id,
        stage_id=stage_id,
        page = page,
        limit = limit
    )
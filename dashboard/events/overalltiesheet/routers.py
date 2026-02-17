from fastapi import APIRouter, Depends
from uuid import UUID
from typing import Optional
from db_connect import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from events.overalltiesheet.services import OverallTiesheetServices

router = APIRouter()

@router.get("")
async def retrieve_overall_points_by_round_and_event(event_id : UUID,db : Annotated[AsyncSession,Depends(get_db_session)],stage_id:Optional[UUID] = None):
    return await OverallTiesheetServices.retrieve_overall_points_by_round_and_event(db=db, event_id=event_id,stage_id=stage_id)
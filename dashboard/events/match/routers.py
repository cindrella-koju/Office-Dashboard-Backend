from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from models import Match, TiesheetPlayer
from uuid import UUID
from sqlalchemy import select, delete
from events.match.schema import CreateMatchRequest, EditMatchRequest
from events.match.services import MatchServices
from events.match.crud import extract_match_by_id
router = APIRouter()



@router.post("")
async def create_match(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    request: CreateMatchRequest,
):
    return await MatchServices.create_match(db=db, request=request)


@router.get("/players")
async def get_tiesheet_player(db: Annotated[AsyncSession,Depends(get_db_session)], tiesheet_id : UUID):
    stmt = select(TiesheetPlayer.id).where(TiesheetPlayer.tiesheet_id == tiesheet_id)
    result = await db.execute(stmt)
    tiesheetplayer_id = result.scalars().all()

    return tiesheetplayer_id

@router.get("/score")
async def get_overall_score(db: Annotated[AsyncSession,Depends(get_db_session)],tiesheet_id:UUID):
    return await MatchServices.get_overall_score(db=db, tiesheet_id=tiesheet_id)


@router.get("/tiesheet/{tiesheet_id}")
async def get_match_detail(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tiesheet_id: UUID
):
    return await MatchServices.get_match_detail(db=db, tiesheet_id=tiesheet_id)

@router.delete("/{match_id}")
async def delete_match(
    db : Annotated[AsyncSession,Depends(get_db_session)],
    match_id : UUID
):
    match_info = await extract_match_by_id(db=db, match_id=match_id)
    
    stmt = delete(Match).where(Match.id == match_id)
    await db.execute(stmt)
    await db.commit()

    return{
        "message" : f"Match {match_info.match_name} deleted successfully"
    }

@router.put("")
async def edit_match(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    request : EditMatchRequest
):
    return await MatchServices.edit_match(db=db, request=request)
    
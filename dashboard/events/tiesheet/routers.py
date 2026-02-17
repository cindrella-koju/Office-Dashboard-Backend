from fastapi import APIRouter, Depends, HTTPException, status
from models import Tiesheet, TiesheetPlayer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session
from events.tiesheet.schema import CreateTiesheet, CreateTiesheetPlayers, EditTiesheetPlayers, TiesheetStatus, UpdateTiesheet
from events.tiesheet.services import TiesheetServices
from events.tiesheet.crud import get_tiesheet

router = APIRouter()

@router.post("")
async def create_tiesheet(
    tiesheet_detail: CreateTiesheet,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    return await TiesheetServices.create_tiesheet(db=db, tiesheet_detail=tiesheet_detail)

@router.post("/player")
async def add_player_in_tiesheet(db: Annotated[AsyncSession, Depends(get_db_session)], player_info : CreateTiesheetPlayers):
    new_player = TiesheetPlayer(
        tiesheet_id=player_info.tiesheet_id,
        user_id=player_info.user_id,
    )

    db.add(new_player)
    await db.commit()

    return{
        "message" : "New Player Added Successfully"
    }

@router.patch("/player")
async def edit_player_in_tiesheet(db: Annotated[AsyncSession, Depends(get_db_session)], player_info : EditTiesheetPlayers,tiesheet_id: UUID, user_id : UUID ):
    stmt = select(TiesheetPlayer).where(TiesheetPlayer.tiesheet_id == tiesheet_id and TiesheetPlayer.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalars().first()

    if player_info.is_winner:
        player.is_winner = player_info.is_winner

    await db.commit()
    return {
        "message" : "Player updated successfully"
    }

@router.get("")
async def retrieve_tiesheet(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_id: UUID,
    stage_id: UUID | None = None,
    today : bool | None = None
):
    return await TiesheetServices.retrieve_tiesheet(db=db, event_id=event_id, stage_id=stage_id, today=today)


@router.get("/{tiesheet_id}")
async def get_tiesheet(
    tiesheet_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    round_id : UUID | None = None
):
    """Get a specific tiesheet by ID with all player info and column values"""
    return await TiesheetServices.get_tiesheet_with_player_info_column_values(db=db, tiesheet_id=tiesheet_id,round_id=round_id)



@router.put("/{tiesheet_id}")
async def update_tiesheet(
    tiesheet_id: UUID,
    tiesheet_detail: UpdateTiesheet,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """Update tiesheet including status, date/time, and player column values"""
    await TiesheetServices.update_tiesheet(db=db, tiesheet_id=tiesheet_id, tiesheet_detail=tiesheet_detail)
    
    
@router.delete("/{tiesheet_id}")
async def delete_tiesheet(
    db: Annotated[AsyncSession,Depends(get_db_session)],
    tiesheet_id : UUID
):
    await get_tiesheet(db=db, tiesheet_id=tiesheet_id)
    
    stmt = delete(Tiesheet).where(Tiesheet.id == tiesheet_id)
    await db.execute(stmt)
    await db.commit()

    return{
        "message" : "Tiesheet deleted successfully"
    }
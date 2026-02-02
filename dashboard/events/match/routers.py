from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated
from models import Match, Tiesheetplayermatchscore, TiesheetPlayer, User, Tiesheet
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

class CreateMatch(BaseModel):
    tiesheet_id : UUID
    match_name : str

class CreateTiesheetPlayerMatchScore(BaseModel):
    tiesheetplayer_id : UUID
    points : str

@router.post("")
async def create_match(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    match_detail: CreateMatch
):
    try:
        new_match = Match(
            tiesheet_id=match_detail.tiesheet_id,
            match_name=match_detail.match_name
        )
        db.add(new_match)
        await db.commit()
        await db.refresh(new_match)

        result = await db.execute(select(Tiesheet).where(Tiesheet.id == match_detail.tiesheet_id))
        tiesheet = result.scalars().first()
        if tiesheet:
            tiesheet.status = "ongoing"
            await db.commit()
        else:
            await db.delete(new_match)
            await db.commit()
            raise HTTPException(status_code=404, detail="Tiesheet not found")

        return {
            "message": "Match added successfully",
            "id": new_match.id
        }

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("{match_id}/score")
async def create_score_of_player(db: Annotated[AsyncSession,Depends(get_db_session)], match_id : UUID, playerscore_detail:CreateTiesheetPlayerMatchScore):
    stmt = Tiesheetplayermatchscore(
        match_id = match_id,
        tiesheetplayer_id = playerscore_detail.tiesheetplayer_id,
        points = playerscore_detail.points
    )

    db.add(stmt)
    await db.commit()

    return {
        "message" : "Match Score added Succesfully"
    }

@router.get("/players")
async def get_tiesheet_player(db: Annotated[AsyncSession,Depends(get_db_session)], tiesheet_id : UUID):
    stmt = select(TiesheetPlayer.id).where(TiesheetPlayer.tiesheet_id == tiesheet_id)
    result = await db.execute(stmt)
    tiesheetplayer_id = result.scalars().all()

    return tiesheetplayer_id

@router.get("/score")
async def get_overall_score(db: Annotated[AsyncSession,Depends(get_db_session)],tiesheet_id:UUID):
    stmt = (
        select(
            Match.match_name,
            func.json_agg(
                func.json_build_object(
                    "username", User.username,
                    "user_id", TiesheetPlayer.user_id,
                    "points", Tiesheetplayermatchscore.points
                )
            ).label("userinfo")
        )
        .join(Tiesheetplayermatchscore, Match.matchscore)
        .join(TiesheetPlayer, Tiesheetplayermatchscore.tiesheetplayer)
        .join(User, User.id == TiesheetPlayer.user_id)
        .where(Match.tiesheet_id == tiesheet_id)
        .group_by(Match.match_name)
    )

    result = await db.execute(stmt)
    score_val = result.mappings().all()

    return score_val
# 3e6e5470-99fa-4d70-9838-8f943b11206e


# c61b2af7-f960-4e68-8b54-a1612efdc87c

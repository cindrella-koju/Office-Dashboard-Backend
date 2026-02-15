from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated, List
from models import Match, Tiesheetplayermatchscore, TiesheetPlayer, User, Tiesheet
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from events.match.services import extract_tiesheet_player_id
router = APIRouter()

class UserInfo(BaseModel):
    points : str | None
    user_id : UUID
    winner : bool

class MatchDetail(BaseModel):
    match_name : str
    userDetail : List[UserInfo]

class CreateMatchRequest(BaseModel):
    overallwinner : UUID | str
    status : str
    tiesheet_id : UUID
    matchDetail : List[MatchDetail]

class CreateTiesheetPlayerMatchScore(BaseModel):
    tiesheetplayer_id : UUID
    points : str

@router.post("")
async def create_match(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    request: CreateMatchRequest,
):
    try:
        # Update tiesheet status if provided
        if request.status:
             stmt = select(Tiesheet).where(Tiesheet.id == request.tiesheet_id)
             result = await db.execute(stmt)
             tiesheet = result.scalars().one_or_none()

             if tiesheet is None:
                 raise HTTPException(status_code=404, detail="Tiesheet not found")

             tiesheet.status = request.status
             db.add(tiesheet)

        # Update overall winner if status is completed and winner is selected
        if request.status == "completed" and request.overallwinner != "":
            stmt = select(TiesheetPlayer).where(
                TiesheetPlayer.tiesheet_id == request.tiesheet_id,
                TiesheetPlayer.user_id == request.overallwinner
            )
            result = await db.execute(stmt)
            tiesheet_player = result.scalars().one_or_none()

            if tiesheet_player is None:
                raise HTTPException(status_code=404, detail="Tiesheet player not found for overall winner")

            tiesheet_player.is_winner = True
            db.add(tiesheet_player)

        # Create matches and their scores
        for match_data in request.matchDetail:
            # Create match
            match = Match(
                tiesheet_id=request.tiesheet_id,
                match_name=match_data.match_name
            )
            db.add(match)
            await db.flush()

            # Create match scores for each user
            for user_detail in match_data.userDetail:
                tiesheetplayer_id = await extract_tiesheet_player_id(
                    db=db,
                    user_id=user_detail.user_id,
                    tiesheet_id=request.tiesheet_id
                )

                if tiesheetplayer_id is None:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Tiesheet player not found for user_id: {user_detail.user_id}"
                    )

                pms = Tiesheetplayermatchscore(
                    match_id=match.id,
                    tiesheetplayer_id=tiesheetplayer_id,
                    points=user_detail.points if user_detail.points else None,
                    winner=user_detail.winner
                )
                db.add(pms)

        await db.commit()
        return {"message": "Match details added successfully"}

    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# @router.post("{match_id}/score")
# async def create_score_of_player(db: Annotated[AsyncSession,Depends(get_db_session)], match_id : UUID, playerscore_detail:CreateTiesheetPlayerMatchScore):
#     stmt = Tiesheetplayermatchscore(
#         match_id = match_id,
#         tiesheetplayer_id = playerscore_detail.tiesheetplayer_id,
#         points = playerscore_detail.points
#     )

#     db.add(stmt)
#     await db.commit()

#     return {
#         "message" : "Match Score added Succesfully"
#     }

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
                    "points", Tiesheetplayermatchscore.points,
                    "winner", Tiesheetplayermatchscore.winner
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

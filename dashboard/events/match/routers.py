from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db_connect import get_db_session
from typing import Annotated, List
from models import Match, Tiesheetplayermatchscore, TiesheetPlayer, User, Tiesheet
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy import select, func, and_, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from events.match.services import extract_tiesheet_player_id
from events.tiesheet.services import get_tiesheet

router = APIRouter()

class UserInfo(BaseModel):
    points : str | None
    user_id : UUID
    winner : bool

class MatchDetail(BaseModel):
    match_name : str
    userDetail : List[UserInfo]

class EditMatchDetail(BaseModel):
    match_id : UUID
    match_name : str
    userDetail : List[UserInfo]

class CreateMatchRequest(BaseModel):
    overallwinner : UUID | str
    status : str
    tiesheet_id : UUID
    matchDetail : List[MatchDetail]

class EditMatchRequest(BaseModel):
    overallwinner : UUID | str
    status : str
    tiesheet_id : UUID
    matchDetail : List[EditMatchDetail]

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
            tiesheet = await get_tiesheet(db=db, tiesheet_id=request.tiesheet_id)

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

        stmt = select(Match).where(Match.tiesheet_id == request.tiesheet_id).options(selectinload(Match.matchscore)).order_by(Match.created_at)
        result = await db.execute(stmt)
        match_info = result.scalars().all()
        
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
                if len(match_info)>0 and match_info[0].matchscore.points is not None:
                    if user_detail.points is None or user_detail.points == "":
                        raise HTTPException(
                            status_code=400,
                            detail="Points are required because the first match already has points"
                        )
                    
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
            Match.created_at,
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
        .group_by(Match.match_name, Match.created_at)
        .order_by(Match.created_at)
    )

    result = await db.execute(stmt)
    score_val = result.mappings().all()

    return score_val


@router.get("/tiesheet/{tiesheet_id}")
async def get_match_detail(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tiesheet_id: UUID
):
    match_user_subq = (
    select(
        Tiesheetplayermatchscore.match_id,
            func.json_agg(
                func.json_build_object(
                    "user_id", TiesheetPlayer.user_id,
                    "points", Tiesheetplayermatchscore.points,
                    "winner", Tiesheetplayermatchscore.winner
                )
            ).label("userDetail")
        )
        .join(TiesheetPlayer, TiesheetPlayer.id == Tiesheetplayermatchscore.tiesheetplayer_id)
        .group_by(Tiesheetplayermatchscore.match_id)
        .subquery()
    )

    # First select matches with their details and created_at for ordering
    match_detail_subq = (
        select(
            Match.tiesheet_id,
            Match.id.label("match_id"),
            Match.match_name,
            Match.created_at,
            match_user_subq.c.userDetail
        )
        .join(match_user_subq, match_user_subq.c.match_id == Match.id)
        .order_by(Match.created_at)
        .subquery()
    )

    # Then aggregate with preserved order
    match_subq = (
        select(
            match_detail_subq.c.tiesheet_id,
            func.json_agg(
                func.json_build_object(
                    "match_id", match_detail_subq.c.match_id,
                    "match_name", match_detail_subq.c.match_name,
                    "userDetail", match_detail_subq.c.userDetail
                )
            ).label("matchDetail")
        )
        .group_by(match_detail_subq.c.tiesheet_id)
        .subquery()
    )

    stmt = (
        select(
            Tiesheet.status,
            TiesheetPlayer.user_id.label("overallwinner"),
            match_subq.c.matchDetail
        )
        .outerjoin(
            TiesheetPlayer,
            and_(
                TiesheetPlayer.tiesheet_id == Tiesheet.id,
                TiesheetPlayer.is_winner == True
            )
        )
        .outerjoin(match_subq, match_subq.c.tiesheet_id == Tiesheet.id)
        .where(Tiesheet.id == tiesheet_id)
    )


    result = await db.execute(stmt)
    row = result.first()

    if not row:
        return None

    return {
        "status": row.status,
        "overallwinner": row.overallwinner,
        "matchDetail": row.matchDetail or [],
    }

@router.delete("/{match_id}")
async def delete_match(
    db : Annotated[AsyncSession,Depends(get_db_session)],
    match_id : UUID
):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match_info = result.scalars().first()

    if not match_info:
        raise HTTPException(
            detail="Match not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
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
    
    print("Request:", request)
    try:

        if request.status != "":
            tiesheet = await get_tiesheet(db = db, tiesheet_id=request.tiesheet_id)

            if tiesheet is None:
                 raise HTTPException(status_code=404, detail="Tiesheet not found")

            tiesheet.status = request.status
            db.add(tiesheet)

        if request.overallwinner != "":
            stmt = select(TiesheetPlayer).where(
                TiesheetPlayer.tiesheet_id == request.tiesheet_id
            )
            result = await db.execute(stmt)
            players = result.scalars().all()

            if not players:
                raise HTTPException(
                    status_code=404,
                    detail="No players found for this tiesheet"
                )
            
            for player in players:
                player.is_winner = False

                db.add(player)

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

            if request.matchDetail:
                stmt = select(Match).where(
                    Match.tiesheet_id == request.tiesheet_id
                ).options(selectinload(Match.matchscore)).order_by(Match.created_at)

                result = await db.execute(stmt)
                match_info = result.scalars().all()

                # Update each match
                for match_data in request.matchDetail:

                    stmt = select(Match).where(
                        Match.id == match_data.match_id,
                        Match.tiesheet_id == request.tiesheet_id
                    ).options(selectinload(Match.matchscore))

                    result = await db.execute(stmt)
                    match = result.scalars().one_or_none()

                    if match is None:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Match not found: {match_data.match_id}"
                        )
                    match.match_name = match_data.match_name
                    db.add(match)

                    # Update user scores
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
                        
                        # Get existing match score
                        stmt = select(Tiesheetplayermatchscore).where(
                            Tiesheetplayermatchscore.match_id == match.id,
                            Tiesheetplayermatchscore.tiesheetplayer_id == tiesheetplayer_id
                        )

                        result = await db.execute(stmt)
                        existing_score = result.scalars().one_or_none()
                        print("Existinf Score:", existing_score)
                        if existing_score is None:
                            raise HTTPException(
                                status_code=404,
                                detail="Match score not found"
                            )

                        existing_score.points = (
                            user_detail.points if user_detail.points != "" else None
                        )
                        print("User winner detail:", user_detail.winner)
                        existing_score.winner = user_detail.winner
                        db.add(existing_score)

            await db.commit()
            return {"message": "Match details updated successfully"}

    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    
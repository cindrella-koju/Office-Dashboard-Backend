from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import TiesheetPlayer, Match, Tiesheetplayermatchscore, User, Tiesheet
from sqlalchemy import select, and_, func
from events.tiesheet.crud import get_tiesheet, extract_tiesheet_player_by_tiesheet_id
from events.match.schema import CreateMatchRequest, EditMatchRequest
from exception import HTTPNotFound, HTTPBadRequest, HTTPInternalServer
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from exception import HTTPNotFound

async def extract_tiesheet_player_id(db:AsyncSession,user_id : UUID, tiesheet_id : UUID):
    stmt = select(TiesheetPlayer.id).where(
        and_(
            TiesheetPlayer.tiesheet_id == tiesheet_id,
            TiesheetPlayer.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    tiesheetplayer_id = result.one_or_none()
    if tiesheetplayer_id is None:
        raise HTTPNotFound("Tiesheet player not available")

    return tiesheetplayer_id[0]

class MatchServices:
    @staticmethod
    async def create_match( db:AsyncSession, request:CreateMatchRequest):
        try:
            # Update tiesheet status if provided
            if request.status:
                tiesheet = await get_tiesheet(db=db, tiesheet_id=request.tiesheet_id)
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
                    raise HTTPNotFound("Tiesheet player not found for overall winner")

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
                            raise HTTPBadRequest("Points are required because the first match already has points")
                        
                    tiesheetplayer_id = await extract_tiesheet_player_id(
                        db=db,
                        user_id=user_detail.user_id,
                        tiesheet_id=request.tiesheet_id
                    )

                    if tiesheetplayer_id is None:
                        raise HTTPNotFound(
                            f"Tiesheet player not found for user_id: {user_detail.user_id}"
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

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer(f"Database error: {str(e)}")
        
    @staticmethod
    async def get_overall_score( db: AsyncSession, tiesheet_id : UUID):
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
    
    @staticmethod
    async def get_match_detail(db: AsyncSession, tiesheet_id : UUID ):
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

        # select matches with their details and created_at for ordering
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
    
    @staticmethod
    async def edit_match( db: AsyncSession, request :EditMatchRequest):
        try:
            if request.status != "":
                tiesheet = await get_tiesheet(db = db, tiesheet_id=request.tiesheet_id)

                tiesheet.status = request.status
                db.add(tiesheet)

            if request.overallwinner != "":
                players = await extract_tiesheet_player_by_tiesheet_id(db=db, tiesheet_id=request.tiesheet_id)
                
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
                    raise HTTPNotFound("Tiesheet player not found for overall winner")

                tiesheet_player.is_winner = True
                db.add(tiesheet_player)

                if request.matchDetail:
                    # Update each match
                    for match_data in request.matchDetail:

                        stmt = select(Match).where(
                            Match.id == match_data.match_id,
                            Match.tiesheet_id == request.tiesheet_id
                        ).options(selectinload(Match.matchscore))

                        result = await db.execute(stmt)
                        match = result.scalars().one_or_none()

                        if match is None:
                            raise HTTPNotFound(f"Match not found: {match_data.match_id}")
                        match.match_name = match_data.match_name
                        db.add(match)

                        # Update user scores
                        for user_detail in match_data.userDetail:
                            tiesheetplayer_id = await extract_tiesheet_player_id(
                                db=db,
                                user_id=user_detail.user_id,
                                tiesheet_id=request.tiesheet_id
                            )
                            # Get existing match score
                            stmt = select(Tiesheetplayermatchscore).where(
                                Tiesheetplayermatchscore.match_id == match.id,
                                Tiesheetplayermatchscore.tiesheetplayer_id == tiesheetplayer_id
                            )

                            result = await db.execute(stmt)
                            existing_score = result.scalars().one_or_none()
                            if existing_score is None:
                                raise HTTPNotFound("Match score not found")

                            existing_score.points = (
                                user_detail.points if user_detail.points != "" else None
                            )
                            print("User winner detail:", user_detail.winner)
                            existing_score.winner = user_detail.winner
                            db.add(existing_score)

                await db.commit()
                return {"message": "Match details updated successfully"}

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer(f"Database error: {str(e)}")

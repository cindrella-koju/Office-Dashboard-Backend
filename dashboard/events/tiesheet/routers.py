from fastapi import APIRouter, Depends, HTTPException, status
from models import Tiesheet, TiesheetPlayer, Group, Stage, Event, User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session
from sqlalchemy.exc import SQLAlchemyError
from events.tiesheet.schema import CreateTiesheet, CreateTiesheetPlayers, EditTiesheetPlayers

router = APIRouter()

@router.post("")
async def create_tiesheet(
    tiesheet_detail: CreateTiesheet,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    try:
        new_tiesheet = Tiesheet(
            group_id=tiesheet_detail.group_id,
            stage_id=tiesheet_detail.stage_id,
            scheduled_date=tiesheet_detail.scheduled_date,
            scheduled_time=tiesheet_detail.scheduled_time
        )

        db.add(new_tiesheet)
        await db.flush()

        tiesheet_players = [
            TiesheetPlayer(
                tiesheet_id=new_tiesheet.id,
                user_id=player,
            )
            for player in tiesheet_detail.players
        ]

        db.add_all(tiesheet_players)

        await db.commit()
        await db.refresh(new_tiesheet)

        return {
            "message" : "Tiesheet Added Successfully",
            "id" :  new_tiesheet.id
        }

    except Exception as e:
        await db.rollback()
        return {
            "message": "Failed to add Tiesheet",
            "error": str(e)
        }

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
    stage_id: UUID | None = None
):
    tp = TiesheetPlayer
    t = Tiesheet
    g = Group
    s = Stage
    e = Event
    u = User
    # Base select
    stmt = (
        select(
            t.id,
            t.scheduled_date,
            t.scheduled_time,
            s.name.label("stage_name"),
            g.name.label("group_name"),
            tp.user_id,
            tp.is_winner,
            u.username
        )
        .join(tp, tp.tiesheet_id == t.id)
        .join(s, s.id == t.stage_id)
        .join(e, e.id == s.event_id)
        .join(u, u.id == tp.user_id)
        .outerjoin(g, g.id == t.group_id)
        .where(e.id == event_id)
    )


    if stage_id:
        stmt = stmt.where(t.stage_id == stage_id)

    result = await db.execute(stmt)
    rows = result.mappings().all()

    tiesheets = {}
    for row in rows:
        tid = row["id"]
        if tid not in tiesheets:
            tie = {
                "id": tid,
                "scheduled_date": row["scheduled_date"],
                "scheduled_time": str(row["scheduled_time"]),
                "stage_name": row["stage_name"],
                "player_info": []
            }
            # Only include group_name if it exists
            if row.get("group_name"):
                tie["group_name"] = row["group_name"]
            tiesheets[tid] = tie

        tiesheets[tid]["player_info"].append({
            "user_id": row["user_id"],
            "is_winner": row["is_winner"],
            "username" : row["username"]
        })

    return list(tiesheets.values())


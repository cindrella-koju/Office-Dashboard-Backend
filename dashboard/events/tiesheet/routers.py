from fastapi import APIRouter, Depends, HTTPException, status
from models import Tiesheet, TiesheetPlayer, Group, Stage, Event, User, StandingColumn, ColumnValues
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, and_
from uuid import UUID
from db_connect import get_db_session
from sqlalchemy.exc import SQLAlchemyError
from events.tiesheet.schema import CreateTiesheet, CreateTiesheetPlayers, EditTiesheetPlayers, TiesheetStatus, UpdateTiesheet
from events.tiesheet.services import extract_standing_column_and_value_of_user, get_tiesheet_with_player, get_tiesheet, update_tiesheet, get_tiesheet_by_id, test_api

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
            status = TiesheetStatus(tiesheet_detail.status),
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
    stage_id: UUID | None = None,
):
    
    rows = await get_tiesheet_with_player(event_id=event_id, db=db)

    if stage_id:
        rows = await get_tiesheet_with_player(event_id=event_id, stage_id=stage_id, db=db)

    tiesheets: dict[UUID, dict] = {}

    for row in rows:
        tid = row["id"]
        sid = row["stage_id"]
        uid = row["user_id"]

        if tid not in tiesheets:
            tiesheet = {
                "id": tid,
                "scheduled_date": row["scheduled_date"],
                "scheduled_time": row["scheduled_time"],
                "stage_id": sid,
                "stage_name": row["stage_name"],
                "status": row["status"],
                "player_info": [],
            }

            if row.get("group_name"):
                tiesheet["group_name"] = row["group_name"]

            tiesheets[tid] = tiesheet

        # Build player entry
        player = {
            "user_id": uid,
            "is_winner": row["is_winner"],
            "username": row["username"],
            "columns": [],
        }

        # Fetch column data for this player
        columns = await extract_standing_column_and_value_of_user(
            user_id=uid,
            stage_id=sid,
            db=db,
        )

        player["columns"] = [
                {
                    "column_field": c.column_field,
                    "value": c.value,
                    "to_show": str(c.to_show),
                }
                for c in columns
            ]
        tiesheets[tid]["player_info"].append(player)

    return list(tiesheets.values())


@router.get("/{tiesheet_id}")
async def get_tiesheet(
    tiesheet_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """Get a specific tiesheet by ID with all player info and column values"""
    
    # Get tiesheet with players
    rows = await get_tiesheet_by_id(db=db, tiesheet_id=tiesheet_id)
    
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tiesheet not found"
        )
    
    # Get column values for all players in this tiesheet
    user_ids = [row["user_id"] for row in rows]
    stage_id = rows[0]["stage_id"]
    
    # Get ALL column values (not just to_show) for editing
    column_values_stmt = (
        select(
            ColumnValues.user_id,
            StandingColumn.column_field,
            ColumnValues.value,
            StandingColumn.id.label("column_id")
        )
        .join(StandingColumn, StandingColumn.id == ColumnValues.column_id)
        .where(
            ColumnValues.user_id.in_(user_ids),
            StandingColumn.stage_id == stage_id
        )
    )
    
    column_result = await db.execute(column_values_stmt)
    column_rows = column_result.mappings().all()
    
    # Build user columns mapping
    user_columns = {}
    for col_row in column_rows:
        user_id = col_row["user_id"]
        if user_id not in user_columns:
            user_columns[user_id] = []
        user_columns[user_id].append({
            "column_name": col_row["column_field"],
            "value": col_row["value"]
        })
    
    # Build response
    first_row = rows[0]
    tiesheet_data = {
        "id": first_row["id"],
        "stage_id": first_row["stage_id"],
        "scheduled_date": first_row["scheduled_date"],
        "scheduled_time": str(first_row["scheduled_time"]),
        "status": first_row["status"],
        "stage_name": first_row["stage_name"],
        "player_info": []
    }
    
    if first_row.get("group_name"):
        tiesheet_data["group_name"] = first_row["group_name"]
    
    for row in rows:
        tiesheet_data["player_info"].append({
            "user_id": row["user_id"],
            "username": row["username"],
            "is_winner": row["is_winner"],
            "columns": user_columns.get(row["user_id"], [])
        })
    
    return tiesheet_data



@router.put("/{tiesheet_id}")
async def update_tiesheet(
    tiesheet_id: UUID,
    tiesheet_detail: UpdateTiesheet,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """Update tiesheet including status, date/time, and player column values"""
    try:
        # Get existing tiesheet
        stmt = select(Tiesheet).where(Tiesheet.id == tiesheet_id)
        result = await db.execute(stmt)
        tiesheet = result.scalar_one_or_none()
        
        if not tiesheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tiesheet not found"
            )
        
        # Update tiesheet fields
        tiesheet.scheduled_date = tiesheet_detail.scheduled_date
        tiesheet.scheduled_time = tiesheet_detail.scheduled_time
        tiesheet.status = TiesheetStatus(tiesheet_detail.status)
        
        # Update player_columns if provided
        if tiesheet_detail.player_columns:
            for player_data in tiesheet_detail.player_columns:
                # Update is_winner status
                player_stmt = select(TiesheetPlayer).where(
                    TiesheetPlayer.tiesheet_id == tiesheet_id,
                    TiesheetPlayer.user_id == player_data.user_id
                )
                player_result = await db.execute(player_stmt)
                tiesheet_player = player_result.scalar_one_or_none()
                
                if tiesheet_player:
                    tiesheet_player.is_winner = player_data.is_winner
                
                # Update column values
                for column_input in player_data.columns:
                    # Check if column value exists
                    cv_stmt = select(ColumnValues).where(
                        ColumnValues.user_id == player_data.user_id,
                        ColumnValues.column_id == column_input.column_id
                    )
                    cv_result = await db.execute(cv_stmt)
                    column_value = cv_result.scalar_one_or_none()
                    
                    if column_value:
                        # Update existing value
                        column_value.value = column_input.value
                    else:
                        # Create new column value
                        new_column_value = ColumnValues(
                            user_id=player_data.user_id,
                            column_id=column_input.column_id,
                            value=column_input.value
                        )
                        db.add(new_column_value)
        
        await db.commit()
        await db.refresh(tiesheet)
        
        return {
            "message": "Tiesheet updated successfully",
            "id": tiesheet.id
        }
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tiesheet: {str(e)}"
        )
    
# @router.get("tttttttttt")
# async def test(db : Annotated[AsyncSession, Depends(get_db_session)], tiesheet_id : UUID):
#     info = await test_api(db, t_id = tiesheet_id)

#     return info
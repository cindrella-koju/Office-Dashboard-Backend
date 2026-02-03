from models import StandingColumn, ColumnValues, Tiesheet, TiesheetPlayer, Stage, Group, User, Event
from sqlalchemy import select, and_, func
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from events.tiesheet.schema import StandingColumnResponse, UpdateTiesheet, TiesheetStatus
import datetime

async def extract_standing_column_and_value_of_user(user_id : UUID, stage_id:UUID, db: AsyncSession):
    stmt = (
        select(StandingColumn.column_field, ColumnValues.value, StandingColumn.stage_id, ColumnValues.user_id, StandingColumn.to_show)
        .join(ColumnValues,StandingColumn.id == ColumnValues.column_id)
        .where(
            and_(
                StandingColumn.stage_id == stage_id,
                ColumnValues.user_id == user_id
            )
        )
    )
    result = await db.execute(stmt)
    column_and_column_val = result.mappings().all()

    return [StandingColumnResponse(**cv) for cv in column_and_column_val]

async def get_tiesheet_with_player(event_id : UUID, db : AsyncSession, stage_id : UUID | None = None, today :bool | None = None):
    stmt = (
        select(
            Tiesheet.id,
            Tiesheet.scheduled_date,
            Tiesheet.scheduled_time,
            Tiesheet.status,
            Stage.name.label("stage_name"),
            Stage.id.label("stage_id"),
            Group.name.label("group_name"),
            TiesheetPlayer.user_id,
            TiesheetPlayer.is_winner,
            User.username,
        )
        .join(TiesheetPlayer, TiesheetPlayer.tiesheet_id == Tiesheet.id)
        .join(Stage, Stage.id == Tiesheet.stage_id)
        .join(Event, Event.id == Stage.event_id)
        .join(User, User.id == TiesheetPlayer.user_id)
        .outerjoin(Group, Group.id == Tiesheet.group_id)
        .where(Event.id == event_id)
    )

    if stage_id:
        stmt = stmt.where(Tiesheet.stage_id == stage_id)

    if today:
        today_date = datetime.date.today()
        stmt = stmt.where(Tiesheet.scheduled_date == today_date)


    result = await db.execute(stmt)
    rows = result.mappings().all()

    return rows

async def get_tiesheet_by_id(db:AsyncSession, tiesheet_id : UUID, round_id : UUID | None = None):
    if round_id:
        stmt = (
        select(
            Tiesheet.id,
            Tiesheet.scheduled_date,
            Tiesheet.scheduled_time,
            Tiesheet.status,
            Stage.name.label("stage_name"),
            Stage.id.label("stage_id"),
            Group.name.label("group_name"),
            Group.id.label("group_id"),
            TiesheetPlayer.user_id,
            TiesheetPlayer.is_winner,
            User.username,
        )
        .join(TiesheetPlayer, TiesheetPlayer.tiesheet_id == Tiesheet.id)
        .join(Stage, Stage.id == Tiesheet.stage_id)
        .join(Event, Event.id == Stage.event_id)
        .join(User, User.id == TiesheetPlayer.user_id)
        .outerjoin(Group, Group.id == Tiesheet.group_id)
        .where(
            and_
                (
                   Tiesheet.id == tiesheet_id,
                   Stage.id == round_id
                )
        )
    )
        
    stmt = (
        select(
            Tiesheet.id,
            Tiesheet.scheduled_date,
            Tiesheet.scheduled_time,
            Tiesheet.status,
            Stage.name.label("stage_name"),
            Stage.id.label("stage_id"),
            Group.name.label("group_name"),
            Group.id.label("group_id"),
            TiesheetPlayer.user_id,
            TiesheetPlayer.is_winner,
            User.username,
        )
        .join(TiesheetPlayer, TiesheetPlayer.tiesheet_id == Tiesheet.id)
        .join(Stage, Stage.id == Tiesheet.stage_id)
        .join(Event, Event.id == Stage.event_id)
        .join(User, User.id == TiesheetPlayer.user_id)
        .outerjoin(Group, Group.id == Tiesheet.group_id)
        .where(Tiesheet.id == tiesheet_id)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()

    return rows

async def test_api(db :AsyncSession, t_id : UUID):
    stmt = (
        select(
            Tiesheet.id,
            Tiesheet.scheduled_date,
            Tiesheet.scheduled_time,
            Tiesheet.status,
            Stage.name.label("stage_name"),
            Stage.id.label("stage_id"),
            Group.name.label("group_name"),
            
            func.json_agg(
                func.json_build_object(
                    "user_id", TiesheetPlayer.user_id,
                    "is_winner", TiesheetPlayer.is_winner,
                    "username",User.username
                )
            ).label("userinfo")
        )
        .join(TiesheetPlayer, TiesheetPlayer.tiesheet_id == Tiesheet.id)
        .join(Stage, Stage.id == Tiesheet.stage_id)
        .join(Event, Event.id == Stage.event_id)
        .join(User, User.id == TiesheetPlayer.user_id)
        .outerjoin(Group, Group.id == Tiesheet.group_id)
        .where(Tiesheet.id == t_id )
        .group_by(
            Tiesheet.id,
            Stage.id,
            Stage.name,
            Group.name
        )
    )
    result = await db.execute(stmt)
    rows = result.mappings().all()

    return rows

async def get_tiesheet(db: AsyncSession, tiesheet_id: UUID) -> Tiesheet | None:
    stmt = select(Tiesheet).where(Tiesheet.id == tiesheet_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_tiesheet(db: AsyncSession, tiesheet: Tiesheet, tiesheet_detail: UpdateTiesheet):
    # Update main fields
    tiesheet.scheduled_date = tiesheet_detail.scheduled_date
    tiesheet.scheduled_time = tiesheet_detail.scheduled_time
    tiesheet.status = TiesheetStatus(tiesheet_detail.status)

    # Update player columns if provided
    if tiesheet_detail.player_columns:
        for player_data in tiesheet_detail.player_columns:
            await update_tiesheet_player(db, tiesheet.id, player_data)

    await db.commit()
    await db.refresh(tiesheet)
    return tiesheet

async def update_tiesheet_player(db: AsyncSession, tiesheet_id: UUID, player_data):
    # Update player winner status
    player_stmt = select(TiesheetPlayer).where(
        TiesheetPlayer.tiesheet_id == tiesheet_id,
        TiesheetPlayer.user_id == player_data.user_id
    )
    player_result = await db.execute(player_stmt)
    tiesheet_player = player_result.scalar_one_or_none()

    if tiesheet_player:
        tiesheet_player.is_winner = player_data.is_winner

    # Update or create column values
    for column_input in player_data.columns:
        cv_stmt = select(ColumnValues).where(
            ColumnValues.user_id == player_data.user_id,
            ColumnValues.column_id == column_input.column_id
        )
        cv_result = await db.execute(cv_stmt)
        column_value = cv_result.scalar_one_or_none()

        if column_value:
            column_value.value = column_input.value
        else:
            new_column_value = ColumnValues(
                user_id=player_data.user_id,
                column_id=column_input.column_id,
                value=column_input.value
            )
            db.add(new_column_value)

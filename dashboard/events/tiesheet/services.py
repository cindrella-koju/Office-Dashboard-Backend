from models import StandingColumn, ColumnValues, Tiesheet, TiesheetPlayer, Stage, Group, User, Event
from sqlalchemy import select, and_, func
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from events.tiesheet.schema import StandingColumnResponse, UpdateTiesheet, TiesheetStatus, CreateTiesheet
import datetime
from exception import HTTPInternalServer, HTTPNotFound, HTTPConflict
from events.tiesheet.crud import get_tiesheet, check_tiesheet_exist, extract_tiesheet_player_by_tiesheet_id
from sqlalchemy.exc import SQLAlchemyError

class TiesheetServices:
    @staticmethod
    async def extract_standing_column_and_value_of_user(user_id : UUID, stage_id:UUID, db: AsyncSession):
        stmt = (
            select(StandingColumn.column_field, ColumnValues.value, StandingColumn.stage_id, ColumnValues.user_id)
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

    @staticmethod
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
                TiesheetPlayer.is_tbd,
                TiesheetPlayer.id.label("tiesheetplayer_id"),
                User.username,
            )
            .join(TiesheetPlayer, TiesheetPlayer.tiesheet_id == Tiesheet.id)
            .join(Stage, Stage.id == Tiesheet.stage_id)
            .join(Event, Event.id == Stage.event_id)
            .outerjoin(User, User.id == TiesheetPlayer.user_id)
            .outerjoin(Group, Group.id == Tiesheet.group_id)
            .where(Event.id == event_id)
            .order_by(Tiesheet.created_at)
        )


        if stage_id:
            stmt = stmt.where(Tiesheet.stage_id == stage_id)

        if today:
            today_date = datetime.date.today()
            stmt = stmt.where(Tiesheet.scheduled_date == today_date)


        result = await db.execute(stmt)
        rows = result.mappings().all()

        return rows

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    async def get_tiesheet(db: AsyncSession, tiesheet_id: UUID) -> Tiesheet | None:
        stmt = select(Tiesheet).where(Tiesheet.id == tiesheet_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
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

    @staticmethod
    async def create_tiesheet(db:AsyncSession, tiesheet_detail : CreateTiesheet):
        tiesheet_exist = await check_tiesheet_exist(db=db, players=tiesheet_detail.players, stage_id=tiesheet_detail.stage_id, tbd_number=tiesheet_detail.tbd_number)
        if tiesheet_exist:
            raise HTTPConflict("Tiesheet already exists")
        
        try:
            if tiesheet_detail.group_id != "":
                new_tiesheet = Tiesheet(
                    group_id=tiesheet_detail.group_id,
                    stage_id=tiesheet_detail.stage_id,
                    scheduled_date=tiesheet_detail.scheduled_date,
                    status = TiesheetStatus(tiesheet_detail.status),
                    scheduled_time=tiesheet_detail.scheduled_time
                )
            else:
                new_tiesheet = Tiesheet(
                    stage_id=tiesheet_detail.stage_id,
                    scheduled_date=tiesheet_detail.scheduled_date,
                    status = TiesheetStatus(tiesheet_detail.status),
                    scheduled_time=tiesheet_detail.scheduled_time
                )

            db.add(new_tiesheet)
            await db.flush()

            if tiesheet_detail.players:
                tiesheet_players = [
                    TiesheetPlayer(
                        tiesheet_id=new_tiesheet.id,
                        user_id=player,
                        is_tbd = False
                    )
                    for player in tiesheet_detail.players
                ]
            
                if tiesheet_detail.tbd_number:
                    tiesheet_players_tbd = [
                        TiesheetPlayer(
                            tiesheet_id = new_tiesheet.id,
                            is_tbd = True
                        )
                        for num in range(tiesheet_detail.tbd_number)
                    ]
                    db.add_all(tiesheet_players_tbd)

                db.add_all(tiesheet_players)

            await db.commit()
            await db.refresh(new_tiesheet)

            return {
                "message" : "Tiesheet Added Successfully",
            }

        except Exception as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to add Tiesheet")
        
    @staticmethod
    async def retrieve_tiesheet(db:AsyncSession, event_id : UUID, stage_id : UUID | None = None, today : bool | None = None):
        rows = await TiesheetServices.get_tiesheet_with_player(event_id=event_id, db=db, today=today)
        if stage_id:
            rows = await TiesheetServices.get_tiesheet_with_player(event_id=event_id, stage_id=stage_id, db=db, today=today)

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
                "id" : row["tiesheetplayer_id"],
                "user_id": uid,
                "is_winner": row["is_winner"],
                "is_tbd" : row["is_tbd"],
                "username": row["username"],
            }

            tiesheets[tid]["player_info"].append(player)

        return list(tiesheets.values())
    
    @staticmethod
    async def get_tiesheet_with_player_info_column_values(
        db:AsyncSession,
        tiesheet_id : UUID,
        round_id : UUID | None = None
    ):
        if round_id:
            rows = await TiesheetServices.get_tiesheet_by_id(db=db, tiesheet_id=tiesheet_id, round_id=round_id)
        # Get tiesheet with players
        rows = await TiesheetServices.get_tiesheet_by_id(db=db, tiesheet_id=tiesheet_id)
        
        if not rows:
            raise HTTPNotFound(
                "Tiesheet not found"
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
                StandingColumn.stage_id == stage_id,

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
            "group_id" : first_row["group_id"],
            "player_info": []
        }
        
        if first_row.get("group_name"):
            tiesheet_data["group_name"] = first_row["group_name"]
        
        for row in rows:
            tiesheet_data["player_info"].append({
                "user_id": row["user_id"],
                "username": row["username"],
                "is_winner": row["is_winner"],
            })
        
        return tiesheet_data
    
    @staticmethod
    async def update_tiesheet(db: AsyncSession, tiesheet_id: UUID, tiesheet_detail: UpdateTiesheet):
        try:
            tiesheet = await get_tiesheet(db=db, tiesheet_id=tiesheet_id)
            tiesheet.scheduled_date = tiesheet_detail.scheduled_date
            tiesheet.scheduled_time = tiesheet_detail.scheduled_time
            tiesheet.status = TiesheetStatus(tiesheet_detail.status)
            
            tiesheet_players_for_validations = await extract_tiesheet_player_by_tiesheet_id(db=db, tiesheet_id=tiesheet_id)
            players = [tpv.user_id for tpv in tiesheet_players_for_validations]
            # Update TBD users
            if tiesheet_detail.tbd_user_ids:
                player_ids = [p.tiesheetplayer_id for p in tiesheet_detail.tbd_user_ids if p.tiesheetplayer_id]
                if player_ids:
                    result = await db.execute(select(TiesheetPlayer).where(TiesheetPlayer.id.in_(player_ids)))
                    tiesheet_players = {tp.id: tp for tp in result.scalars().all()}
                    for player in tiesheet_detail.tbd_user_ids:
                        players.append(player.user_id)
                        tiesheet_exist = await check_tiesheet_exist(db=db, players=players, stage_id=tiesheet_detail.stage_id)
                        if tiesheet_exist:
                            raise HTTPConflict("Tiesheet already exists")
                        tp = tiesheet_players.get(player.tiesheetplayer_id)
                        if tp:
                            tp.user_id = player.user_id
                            tp.is_tbd = False
                        else:
                            print(f"Warning: TiesheetPlayer {player.tiesheetplayer_id} not found")

            # Add new TBD players
            if tiesheet_detail.tbd_number:
                new_tbd = [TiesheetPlayer(tiesheet_id=tiesheet_id, is_tbd=True) for _ in range(tiesheet_detail.tbd_number)]
                db.add_all(new_tbd)

            # Edit existing user info
            if tiesheet_detail.edit_user_info:
                tie_ids = [p.old_user_tiesheet_id for p in tiesheet_detail.edit_user_info if p.old_user_tiesheet_id]
                if tie_ids:
                    result = await db.execute(select(TiesheetPlayer).where(TiesheetPlayer.id.in_(tie_ids)))
                    tie_map = {tp.id: tp for tp in result.scalars().all()}
                    for py in tiesheet_detail.edit_user_info:
                        tp = tie_map.get(py.old_user_tiesheet_id)
                        if tp:
                            tp.user_id = py.new_user_id
                        else:
                            print(f"Warning: TiesheetPlayer {py.old_user_tiesheet_id} not found")

            await db.commit()
            await db.refresh(tiesheet)
            return {"message": "Tiesheet updated successfully", "id": tiesheet.id}

        except Exception as e:
            await db.rollback()
            raise HTTPInternalServer(f"Failed to update tiesheet: {str(e)}")
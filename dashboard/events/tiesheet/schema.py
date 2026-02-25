from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List
from datetime import date, time
from enum import Enum


class TiesheetStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    ongoing = "ongoing"


class CreateTiesheetPlayers(BaseModel):
    tiesheet_id: UUID
    user_id: UUID


class EditTiesheetPlayers(BaseModel):
    is_winner: bool | None = None


class CreateTiesheet(BaseModel):
    group_id: UUID | str | None = None
    stage_id: UUID
    scheduled_date: date
    scheduled_time: time
    status: TiesheetStatus
    players: List[UUID]
    tbd_number : int | None = None


class ColumnValueInput(BaseModel):
    column_id: UUID
    value: str


class PlayerColumnData(BaseModel):
    user_id: UUID
    is_winner: bool
    columns: List[ColumnValueInput]


class UpdateTiesheet(BaseModel):
    stage_id: UUID | None = None
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    status: TiesheetStatus | None = None
    tbd_user_ids : List[TBDUserIds] | None = None
    edit_user_info : List[EditUserInfo] | None = None
    tbd_number : int | None = None

class TBDUserIds(BaseModel):
    tiesheetplayer_id : UUID
    user_id : UUID

class EditUserInfo(BaseModel):
    new_user_id : UUID | str
    old_user_tiesheet_id : UUID | str
    old_user_id : UUID | str

class StandingColumnResponse(BaseModel):
    column_field : str
    value : str | None
    stage_id : UUID
    user_id : UUID
    to_show : bool

    model_config = ConfigDict(from_attributes=True)

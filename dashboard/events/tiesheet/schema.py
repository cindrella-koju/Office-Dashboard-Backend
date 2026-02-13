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


class ColumnValueInput(BaseModel):
    column_id: UUID
    value: str


class PlayerColumnData(BaseModel):
    user_id: UUID
    is_winner: bool
    columns: List[ColumnValueInput]


class UpdateTiesheet(BaseModel):
    stage_id: UUID
    players: List[UUID]
    scheduled_date: date 
    scheduled_time: time 
    status: TiesheetStatus
    player_columns: List[PlayerColumnData] | None = None

class StandingColumnResponse(BaseModel):
    column_field : str
    value : str | None
    stage_id : UUID
    user_id : UUID
    to_show : bool

    model_config = ConfigDict(from_attributes=True)

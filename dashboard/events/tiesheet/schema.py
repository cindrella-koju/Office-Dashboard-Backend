from pydantic import BaseModel
from uuid import UUID
from typing import List
from datetime import date, time

class CreateTiesheetPlayers(BaseModel):
    tiesheet_id : UUID
    user_id : UUID

class EditTiesheetPlayers(BaseModel):
    is_winner : bool | None = None

class CreateTiesheet(BaseModel):
    group_id : UUID | None = None
    stage_id : UUID
    scheduled_date : date
    scheduled_time : time
    players : List[UUID]


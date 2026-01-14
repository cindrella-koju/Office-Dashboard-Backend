from pydantic import BaseModel
import uuid
from typing import Optional

class StageDetail(BaseModel):
    event_id : uuid.UUID
    name : str
    round_order : int

class EditStageDetail(BaseModel):
    name : Optional[str] = None
    round_order : Optional[int] = None

class CreateStateForm(BaseModel):
    name : str
    round_order : int

class StageResponse(StageDetail):
    id : uuid.UUID
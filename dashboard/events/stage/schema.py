from pydantic import BaseModel,ConfigDict
from typing import List
import uuid
from typing import Optional

class StageDetail(BaseModel):
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
    name : str | None = None
    
    model_config = ConfigDict(from_attributes=True)

class RoundInfo(BaseModel):
    id : uuid.UUID
    name :  str

    model_config = ConfigDict(from_attributes=True)
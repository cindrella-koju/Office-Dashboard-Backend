from pydantic import BaseModel, ConfigDict
from uuid import UUID

class QualifierByRound(BaseModel):
    id : UUID
    username : str

    model_config = ConfigDict(from_attributes=True)

class QualifierModel(BaseModel):
    user_id : list[UUID]
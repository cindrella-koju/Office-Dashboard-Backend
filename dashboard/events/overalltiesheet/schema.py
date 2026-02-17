from typing import List, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ColumnDetail(BaseModel):
    column_name: str
    column_value: str

class User(BaseModel):
    user_id: UUID
    username: str
    column_detail: List[ColumnDetail]

class Round(BaseModel):
    round_name: str
    users: List[User]

    model_config = ConfigDict(from_attributes=True)
    
ResponseSchema = Dict[str, Round]
 
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List

class GroupDetail(BaseModel):
    round_id : UUID
    name : str
    participants_id : List[UUID]

class EditGroupDetail(BaseModel):
    stage_id : Optional[UUID] = None
    name : Optional[str] = None

class GroupUpdate(BaseModel):
    name: str | None = None
    stage_id: int | None = None

class AddGroupMember(BaseModel):
    group_id : UUID
    user_id : UUID
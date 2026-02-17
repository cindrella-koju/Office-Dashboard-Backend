from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List

class GroupDetail(BaseModel):
    round_id : UUID
    name : str
    participants_ids : List[UUID]

class EditGroupDetail(BaseModel):
    stage_id : Optional[UUID] = None
    name : Optional[str] = None

class GroupUpdate(BaseModel):
    name: str | None = None
    round_id : UUID | None = None
    participants_ids: List[UUID] | None = None

class AddGroupMember(BaseModel):
    group_id : UUID
    user_id : UUID

class ColumnValueUpdate(BaseModel):
    column_id: UUID
    value: str | None

class MemberColumnUpdate(BaseModel):
    user_id: UUID
    columns: List[ColumnValueUpdate]

class GroupTableUpdate(BaseModel):
    members: List[MemberColumnUpdate]

class GroupEvent(BaseModel):
    id : UUID
    groupname : str

    model_config = ConfigDict(from_attributes=True)

class GroupByRound(BaseModel):
    id : UUID
    name : str

    model_config = ConfigDict(from_attributes=True)

class GroupMember(BaseModel):
    id: UUID
    username : str

    model_config = ConfigDict(from_attributes=True)
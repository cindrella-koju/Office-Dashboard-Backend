from pydantic import BaseModel
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
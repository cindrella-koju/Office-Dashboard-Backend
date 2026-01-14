from pydantic import BaseModel
from uuid import UUID

class CreateColumn(BaseModel):
    stage_id : UUID
    column_field : str

class ColumnResponse(CreateColumn):
    id : UUID

class EditColumn(BaseModel):
    stage_id : UUID | None = None
    column_field : str | None = None

class CreateValues(BaseModel):
    column_id : UUID
    user_id : UUID
    value : str

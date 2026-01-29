from pydantic import BaseModel,ConfigDict
from uuid import UUID

class CreateColumn(BaseModel):
    stage_id : UUID
    column_field : str
    default_value : str
    to_show : str

class ColumnResponse(CreateColumn):
    id : UUID
    column_field : str
    default_value : str
    to_show : bool

    model_config = ConfigDict(from_attributes=True)

class EditColumn(BaseModel):
    stage_id : UUID | None = None
    column_field : str | None = None
    to_show : str

class CreateValues(BaseModel):
    column_id : UUID
    user_id : UUID
    value : str

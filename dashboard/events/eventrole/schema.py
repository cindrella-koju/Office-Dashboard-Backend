from pydantic import BaseModel, ConfigDict
from uuid import UUID

class createEventRole(BaseModel):
    user_id : UUID
    role_id : UUID

class EventRoleResponse(BaseModel):
    id : UUID
    user_id : UUID
    username : str
    role_id : UUID
    rolename : str

    model_config = ConfigDict(from_attributes=True)

class EditEventRole(BaseModel):
    user_id : UUID | str | None = None 
    role_id : UUID | str | None = None 
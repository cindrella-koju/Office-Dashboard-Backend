from pydantic import BaseModel, ConfigDict
from enum import Enum
from datetime import datetime
from uuid import UUID

class RoleEnum(str,Enum):
    admin = "admin"
    superadmin = "superadmin"
    member = "member"
    
class UserDetail(BaseModel):
    username : str
    fullname : str
    email : str
    password : str
    role_id : UUID | None = None

class EditUserDetail(BaseModel):
    username : str | None = None
    fullname : str | None = None
    email : str | None = None
    role_id : UUID | None = None

class UserDetailResponse(BaseModel):
    id : UUID
    username : str
    fullname : str
    email : str
    role_id : UUID
    rolename : str

    model_config = ConfigDict(from_attributes=True)

class LoginUser(BaseModel):
    username : str
    password : str
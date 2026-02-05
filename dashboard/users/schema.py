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
    role : RoleEnum
    password : str

class EditUserDetail(BaseModel):
    username : str | None = None
    fullname : str | None = None
    email : str | None = None
    role : RoleEnum | None = None

class UserDetailResponse(BaseModel):
    id : UUID
    username : str
    fullname : str
    email : str
    created_at : datetime
    updated_at : datetime

    model_config = ConfigDict(from_attributes=True)

class LoginUser(BaseModel):
    username : str
    password : str

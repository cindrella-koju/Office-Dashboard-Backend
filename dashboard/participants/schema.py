from pydantic import BaseModel,ConfigDict
from typing import List
from uuid import UUID

class Participants(BaseModel):
    user_id : UUID
    event_id : UUID

class ParticipantsEventResponse(BaseModel):
    user_id : UUID
    event_id : UUID
    is_winner : bool
    username : str

class ParticipantsUserResponse(BaseModel):
    user_id : UUID
    event_id : UUID
    is_winner : bool
    username : str
    title : str


class RoundInfo(BaseModel):
    id : UUID
    name :  str

    model_config = ConfigDict(from_attributes=True)
    
class UserResponse(BaseModel):
    id : UUID
    username : str

    model_config = ConfigDict(from_attributes=True)

class CreateGroupResponse(BaseModel):
    round : List[RoundInfo]
    group_name : str
    participants : List[UserResponse]

    model_config = ConfigDict(from_attributes=True)
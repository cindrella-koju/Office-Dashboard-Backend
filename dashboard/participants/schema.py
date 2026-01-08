from pydantic import BaseModel
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
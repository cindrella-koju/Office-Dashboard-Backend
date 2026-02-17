from pydantic import BaseModel
from uuid import UUID
from typing import List

class UserInfo(BaseModel):
    points : str | None
    user_id : UUID
    winner : bool

class MatchDetail(BaseModel):
    match_name : str
    userDetail : List[UserInfo]

class EditMatchDetail(BaseModel):
    match_id : UUID
    match_name : str
    userDetail : List[UserInfo]

class CreateMatchRequest(BaseModel):
    overallwinner : UUID | str
    status : str
    tiesheet_id : UUID
    matchDetail : List[MatchDetail]

class EditMatchRequest(BaseModel):
    overallwinner : UUID | str
    status : str
    tiesheet_id : UUID
    matchDetail : List[EditMatchDetail]

class CreateTiesheetPlayerMatchScore(BaseModel):
    tiesheetplayer_id : UUID
    points : str
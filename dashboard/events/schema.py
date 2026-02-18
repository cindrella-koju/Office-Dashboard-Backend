from pydantic import BaseModel, ConfigDict
from datetime import date
from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Optional

class StatusEnum(str,Enum):
    draft = "draft"
    active = "active"
    completed = "completed"

class EventDetail(BaseModel):
    title : str
    description : str | None = None
    startdate : date
    enddate : date
    status : StatusEnum

    model_config = ConfigDict(from_attributes=True)
    
class EditEventDetail(BaseModel):
    title : str | None = None
    description : str | None = None
    startdate : date | None = None
    enddate : date | None = None
    status :Optional[StatusEnum] = None

class EventDetailResponse(EventDetail):
    id : UUID
    created_at : datetime
    updated_at : datetime

    model_config = ConfigDict(from_attributes=True)

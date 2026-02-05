from pydantic import BaseModel, ConfigDict
from uuid import UUID

class RolePermission(BaseModel):
    rolename : str
    can_edit : bool
    can_create : bool
    can_delete : bool
    can_edit_roles : bool
    can_create_roles : bool
    can_delete_roles : bool
    can_edit_users : bool
    can_create_users : bool
    can_delete_users : bool
    can_edit_events : bool
    can_create_events : bool
    can_delete_events : bool
    can_manage_events : bool
    home_page : bool
    event_page : bool
    user_page : bool
    profile_page : bool
    tiesheet_page : bool
    group_page : bool
    round_config_page : bool
    qualifier_page : bool
    participants_page : bool
    column_config_page : bool
    group_stage_standing_page : bool
    todays_game_page : bool
    role_page : bool

class RoleResponse(BaseModel):
    id : UUID
    rolename : str
    can_edit : bool
    can_create : bool
    can_delete : bool
    can_edit_roles : bool
    can_create_roles : bool
    can_delete_roles : bool
    can_edit_users : bool
    can_create_users : bool
    can_delete_users : bool
    can_edit_events : bool
    can_create_events : bool
    can_delete_events : bool

    can_manage_events : bool
    roleaccesspage : RolePageAccessResponse

    model_config = ConfigDict(from_attributes=True)

class RolePageAccessResponse(BaseModel):
    home_page : bool
    event_page : bool
    user_page : bool
    profile_page : bool
    role_page : bool
    tiesheet_page : bool
    group_page : bool
    round_config_page : bool
    qualifier_page : bool
    participants_page : bool
    column_config_page : bool
    group_stage_standing_page : bool
    todays_game_page : bool

    model_config = ConfigDict(from_attributes=True)

class EventRole(BaseModel):
    user_id : UUID
    event_id : UUID | None = None
    role_id : UUID

class UserEventRole(BaseModel):
    id : UUID
    rolename : str
    can_create : bool
    can_delete : bool
    can_edit : bool
    roleaccesspage :RolePageAccessResponse

    model_config = ConfigDict(from_attributes=True)

class EventRoleResponse(BaseModel):
    role : UserEventRole

    model_config = ConfigDict(from_attributes=True)


class RoleDetail(BaseModel):
    id : UUID
    rolename : str
    can_edit_roles : bool
    can_create_roles : bool
    can_delete_roles : bool

    model_config = ConfigDict(from_attributes=True)

class EventDetail(BaseModel):
    id : UUID
    rolename : str
    can_edit_events : bool
    can_create_events : bool
    can_delete_events : bool

    model_config = ConfigDict(from_attributes=True)

class UserDetail(BaseModel):
    id : UUID
    rolename : str
    can_edit_users : bool
    can_create_users : bool
    can_delete_users : bool

    model_config = ConfigDict(from_attributes=True)

class WithinEventDetail(BaseModel):
    id : UUID
    rolename : str
    can_edit : bool
    can_create : bool
    can_delete : bool

    model_config = ConfigDict(from_attributes=True)
    
class PageDetail(BaseModel):
    id : UUID
    rolename : str
    roleaccesspage :RolePageAccessResponse

from pydantic import BaseModel, ConfigDict
from uuid import UUID

class RolePermission(BaseModel):
    rolename : str
    can_view : bool
    can_edit : bool
    can_create : bool
    can_delete : bool
    can_view_roles : bool
    can_edit_roles : bool
    can_create_roles : bool
    can_delete_roles : bool
    can_view_users : bool
    can_edit_users : bool
    can_create_users : bool
    can_delete_users : bool
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

class RoleResponse(BaseModel):
    id : UUID
    rolename : str
    can_view : bool
    can_edit : bool
    can_create : bool
    can_delete : bool
    can_view_roles : bool
    can_edit_roles : bool
    can_create_roles : bool
    can_delete_roles : bool
    can_view_users : bool
    can_edit_users : bool
    can_create_users : bool
    can_delete_users : bool

    can_manage_events : bool
    roleaccesspage : RolePageAccessResponse

    model_config = ConfigDict(from_attributes=True)

class RolePageAccessResponse(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)
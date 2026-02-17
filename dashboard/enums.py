import enum
from roles.schema import RoleDetail, RoleDetail, EventDetail, UserDetail, WithinEventDetail, PageDetail

class PermissionDetailEnum(enum.Enum):
    role = "role"
    event = "event"
    user = "user"
    within_event = "within_event"
    page = "page"

PERMISSION_DETAIL_SCHEMA = {
    "role" : RoleDetail,
    "event" : EventDetail,
    "user" : UserDetail,
    "within_event" : WithinEventDetail,
    "page" : PageDetail
}
from fastapi import APIRouter, FastAPI, Query
from pydantic import BaseModel
from enum import Enum
from typing import Union, get_args, get_origin
from events.schema import EditEventDetail, EventDetail
from users.schema import UserDetail, EditUserDetail
from events.stage.schema import CreateStateForm, EditStageDetail 

router = APIRouter()
app = FastAPI()
app.include_router(router, prefix="/fields")

def model_to_field_schema(model: BaseModel):
    schema = {}
    for name, field in model.model_fields.items():  # Pydantic v2
        field_type = field.annotation

        # If Enum
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            schema[name] = [e.value for e in field_type]

        # If Union (includes Optional)
        elif get_origin(field_type) is Union:
            types = get_args(field_type)
            enum_values = None
            none_included = False
            other_types = []

            for t in types:
                if t is type(None):
                    none_included = True
                elif isinstance(t, type) and issubclass(t, Enum):
                    enum_values = [e.value for e in t]
                else:
                    other_types.append(t.__name__)

            # Build readable schema
            if enum_values is not None:
                if none_included:
                    schema[name] = f"{enum_values} or None"
                else:
                    schema[name] = enum_values
            elif other_types:
                if none_included:
                    schema[name] = " or ".join(other_types) + " or None"
                else:
                    schema[name] = " or ".join(other_types)

        # Otherwise
        else:
            schema[name] = field_type.__name__

    return schema


# ----- API -----
@router.get("/createfield")
async def generate_create_field(page: str = Query(..., description="Page type, e.g., event or user")):
    if page == "event":
        return model_to_field_schema(EventDetail)
    elif page == "user":
        return model_to_field_schema(UserDetail)
    elif page == "stage":
        return model_to_field_schema(CreateStateForm)
    else:
        return {"error": "Unknown page type"}
    

@router.get("/editfield")
async def generate_edit_field(page: str = Query(..., description="Page type, e.g., event or user")):
    if page == "event":
        return model_to_field_schema(EditEventDetail)
    elif page == "user":
        return model_to_field_schema(EditUserDetail)
    elif page == "stage":
        return model_to_field_schema(EditStageDetail)
    else:
        return {
            "error" : "Unknown page type"
        }
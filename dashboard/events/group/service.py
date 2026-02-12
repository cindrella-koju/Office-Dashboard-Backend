from sqlalchemy.ext.asyncio import AsyncSession 
from uuid import UUID
from models import Group, Stage, User, ColumnValues, GroupMembers, StandingColumn
from fastapi import HTTPException, status
from sqlalchemy import select, and_
from events.services import EventServices

class GroupServices:
    @staticmethod
    async def validate_group(
        db : AsyncSession,
        group_id : UUID
    ):
        result = await db.execute(select(Group).where(Group.id == group_id))
        group =result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Group not found"
            )
        
    @staticmethod
    async def get_group_detail_in_event_services(
        db:AsyncSession,
        event_id : UUID
    ):  
        await EventServices.validate_event(db = db,event_id=event_id)
        query = (
            select(
                Stage.id.label("stage_id"),
                Stage.name.label("stage_name"),
                User.username.label("username"),
                GroupMembers.user_id,
                Group.id.label("group_id"),
                Group.name.label("group_name"),
                StandingColumn.column_field.label("column_name"),
                StandingColumn.id.label("column_id"),
                ColumnValues.value.label("column_value")
            )
            .join(Group, Group.id == GroupMembers.group_id)
            .join(Stage, Stage.id == Group.stage_id)
            .join(StandingColumn,StandingColumn.stage_id == Stage.id)
            .join(ColumnValues, and_(ColumnValues.column_id == StandingColumn.id, ColumnValues.user_id == GroupMembers.user_id))
            .join(User,User.id == GroupMembers.user_id)
            .where(
                and_(
                    Group.event_id == event_id,
                    Stage.event_id == event_id
                ))
        )


        result = await db.execute(query)
        detail = result.mappings().all()

        return await GroupServices.format_group_data(detail)
    

    @staticmethod
    async def format_group_data(rows):
        group_dict = {}
        for row in rows:
            sid = row.stage_id
            gid = row.group_id
            uid = row.user_id
            if sid not in group_dict:
                group_dict[sid] = {
                    "stage_id": row.stage_id,
                    "stage_name" : row.stage_name,
                    "groups" : {}
                }
            if gid not in group_dict[sid]["groups"]:
                group_dict[sid]["groups"][gid] = {
                    "group_id": row.group_id,
                    "group_name": row.group_name,
                    "members": {}
                }

            if uid not in group_dict[sid]["groups"][gid]["members"]:
                group_dict[sid]["groups"][gid]["members"][uid] = {
                    "user_id": row.user_id,
                    "username": row.username,
                    "columns": []
                }

            group_dict[sid]["groups"][gid]["members"][uid]["columns"].append({
                "column_id": row.column_id,
                "column_field": row.column_name,
                "value": row.column_value
            })

        for gdata in group_dict.values():
            gdata["groups"] = list(gdata["groups"].values())
            for group in gdata["groups"]:
                group["members"] = list(group["members"].values())

        return list(group_dict.values())
from sqlalchemy.ext.asyncio import AsyncSession 
from uuid import UUID
from models import Group, Stage, User, ColumnValues, GroupMembers, StandingColumn
from fastapi import HTTPException, status
from sqlalchemy import select, and_, delete
from events.crud import extract_event_by_id
from exception import HTTPNotFound
from events.group.schema import GroupDetail, GroupUpdate, GroupTableUpdate
from sqlalchemy.exc import SQLAlchemyError
from exception import HTTPNotFound, HTTPInternalServer
from events.group.crud import extract_group_by_id
from sqlalchemy.orm import aliased

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
        event = await extract_event_by_id(db = db,event_id=event_id)
        if not event:
            HTTPNotFound("Event not found")

        columns_subq = (
            select(
                StandingColumn.id.label("column_id"),
                StandingColumn.stage_id.label("stage_id"),
                StandingColumn.column_field.label("column_name"),
                StandingColumn.created_at.label("column_created_at")
            )
            .order_by(StandingColumn.created_at, StandingColumn.id)  # Ensure stable order
        ).subquery()

        ColumnsAlias = aliased(StandingColumn, columns_subq)
        query = (
            select(
                Stage.id.label("stage_id"),
                Stage.name.label("stage_name"),
                User.username.label("username"),
                GroupMembers.user_id,
                Group.id.label("group_id"),
                Group.name.label("group_name"),
                columns_subq.c.column_name,
                columns_subq.c.column_id,
                ColumnValues.value.label("column_value")
            )
            .join(Group, Group.id == GroupMembers.group_id)
            .join(Stage, Stage.id == Group.stage_id)
            # Join the ordered columns subquery
            .join(columns_subq, columns_subq.c.stage_id == Stage.id)
            # Join ColumnValues matching user and column
            .join(
                ColumnValues,
                and_(
                    ColumnValues.column_id == columns_subq.c.column_id,
                    ColumnValues.user_id == GroupMembers.user_id
                )
            )
            .join(User, User.id == GroupMembers.user_id)
            .where(
                and_(
                    Group.event_id == event_id,
                    Stage.event_id == event_id
                )
            )
            # Order by user first, then column created_at (already enforced in subquery)
            .order_by(
                User.created_at,
                columns_subq.c.column_created_at,
                columns_subq.c.column_id  # tiebreaker for stable order
            )
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
    
    @staticmethod
    async def create_group(db:AsyncSession, event_id : UUID, group:GroupDetail):
        try:
            new_group = Group(
                stage_id=group.round_id,
                name=group.name,
                event_id= event_id
            )

            db.add(new_group)
            await db.flush() 

            members = [
                GroupMembers(group_id=new_group.id, user_id=user_id)
                for user_id in group.participants_ids
            ]
            db.add_all(members)

            await db.commit()

            return {
                "message" : f"Group {group.name} created successfully"
            }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to create group")
        
    @staticmethod
    async def update_group(db:AsyncSession, group_update:GroupUpdate, group_id : UUID):
        try:
            group = await extract_group_by_id(db=db, group_id=group_id)

            if group_update.name is not None:
                group.name = group_update.name

            # Update participants if provided
            if group_update.participants_ids is not None:
                # Delete existing members
                await db.execute(delete(GroupMembers).where(GroupMembers.group_id == group_id))
                
                # Add new members
                new_members = [
                    GroupMembers(group_id=group_id, user_id=user_id)
                    for user_id in group_update.participants_ids
                ]
                db.add_all(new_members)

                await db.commit()
                return {
                    "message": f"Group {group.name} successfully",
                }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to update group") 
        
    @staticmethod
    async def update_group_table_data( db : AsyncSession, group_id : UUID, table_update : GroupTableUpdate ):
        try:
            for member_data in table_update.members:
                for column_data in member_data.columns:
                    # Check if column value exists
                    stmt = select(ColumnValues).where(
                        ColumnValues.user_id == member_data.user_id,
                        ColumnValues.column_id == column_data.column_id
                    )
                    result = await db.execute(stmt)
                    existing_value = result.scalar_one_or_none()

                    if existing_value:
                        # Update existing value
                        existing_value.value = column_data.value
                    else:
                        # Create new column value
                        new_value = ColumnValues(
                            user_id=member_data.user_id,
                            column_id=column_data.column_id,
                            value=column_data.value
                        )
                        db.add(new_value)
            
            await db.commit()
            return {
                "message": "Group table data updated successfully",
            }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to update group table data")
        
    @staticmethod
    async def delete_group_member( db: AsyncSession, group_id :UUID, user_id : UUID):
        stmt = (
            select(GroupMembers, User.username, Group.name)
            .join(User, GroupMembers.user_id == User.id)
            .join(Group, GroupMembers.group_id == Group.id)
            .where(
                GroupMembers.user_id == user_id,
                GroupMembers.group_id == group_id
            )
        )
        result = await db.execute(stmt)
        row = result.one_or_none()

        if not row:
            raise HTTPNotFound("Group Member not found")
        
        _, username, group_name = row

        await db.execute(
            delete(GroupMembers).where(
                GroupMembers.user_id == user_id,
                GroupMembers.group_id == group_id
            )
        )
        await db.commit()
        return {
            "message": f"Member {username} removed from group {group_name} successfully"
        }
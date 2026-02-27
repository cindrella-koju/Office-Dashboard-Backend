from sqlalchemy.ext.asyncio import AsyncSession 
from uuid import UUID
from models import Group, Stage, User, ColumnValues, GroupMembers, StandingColumn, User
from fastapi import HTTPException, status
from sqlalchemy import select, and_, delete, func, case, cast, Integer
from events.crud import extract_event_by_id
from exception import HTTPNotFound
from events.group.schema import GroupDetail, GroupUpdate, GroupTableUpdate
from sqlalchemy.exc import SQLAlchemyError
from exception import HTTPNotFound, HTTPInternalServer
from events.group.crud import extract_group_by_id
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import aggregate_order_by

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
        event_id : UUID,
        stage_id : UUID | None = None
    ):  
        try:
             # Extract the event to ensure it exists
            event = await extract_event_by_id(db=db, event_id=event_id)
            if not event:
                raise HTTPException(status_code=404, detail="Event not found")

            # Columns per user per stage
            columns_subq = (
                select(
                    StandingColumn.stage_id.label("stage_id"),
                    ColumnValues.user_id.label("user_id"),
                    func.json_agg(
                        aggregate_order_by(
                            func.json_build_object(
                                "column_id", StandingColumn.id,
                                "column_field", StandingColumn.column_field,
                                "value", ColumnValues.value,
                                "created_at", StandingColumn.created_at
                            ),
                            StandingColumn.created_at.asc(),
                            StandingColumn.id.asc()  # tie-breaker if created_at is same
                        )
                    ).label("columns")
                )
                .join(ColumnValues, ColumnValues.column_id == StandingColumn.id)
                .group_by(StandingColumn.stage_id, ColumnValues.user_id)
            ).subquery()

            # Total points per user per stage
            user_points_subq = (
                select(
                    ColumnValues.user_id.label("user_id"),
                    StandingColumn.stage_id.label("stage_id"),
                    func.sum(
                        case(
                            (func.lower(StandingColumn.column_field) == "points",
                             cast(ColumnValues.value, Integer)),
                            else_=0
                        )
                    ).label("total_points")
                )
                .join(StandingColumn, StandingColumn.id == ColumnValues.column_id)
                .group_by(ColumnValues.user_id, StandingColumn.stage_id)
            ).subquery()

            # Groups with members, ordering members by total_points DESC
            groups_subq = (
                select(
                    Group.id.label("group_id"),
                    Group.name.label("group_name"),
                    Group.stage_id.label("stage_id"),
                    func.json_agg(
                        aggregate_order_by(
                            func.json_build_object(
                                "user_id", GroupMembers.user_id,
                                "username", User.username,
                                "columns", columns_subq.c.columns
                            ),
                            user_points_subq.c.total_points.desc(),
                            User.username.asc()  # optional tie-breaker
                        )
                    ).filter(GroupMembers.user_id.is_not(None)).label("members")
                )
                .outerjoin(GroupMembers, GroupMembers.group_id == Group.id)
                .outerjoin(User, User.id == GroupMembers.user_id)
                .outerjoin(columns_subq,
                           (columns_subq.c.user_id == GroupMembers.user_id)
                           & (columns_subq.c.stage_id == Group.stage_id)
                )
                .outerjoin(user_points_subq,
                           (user_points_subq.c.user_id == GroupMembers.user_id)
                           & (user_points_subq.c.stage_id == Group.stage_id)
                )
                .group_by(Group.id, Group.name, Group.stage_id)
            ).subquery()

            # Stages with groups
            stmt = (
                select(
                    Stage.id.label("stage_id"),
                    Stage.name.label("stage_name"),
                    func.json_agg(
                        func.json_build_object(
                            "group_id", groups_subq.c.group_id,
                            "group_name", groups_subq.c.group_name,
                            "members", groups_subq.c.members
                        )
                    ).label("groups")
                )
                .join(groups_subq, groups_subq.c.stage_id == Stage.id)
                .group_by(Stage.id, Stage.name)
                .where(Stage.id == stage_id)  # optional filter
            )

            result = await db.execute(stmt)
            detail = result.mappings().all()
            return detail

        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error occurred: {e}")
        except SQLAlchemyError as e:
            raise HTTPInternalServer(f"Database error occured:{e}")
        
    
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
            
            stmt = select(StandingColumn.id.label("id"), StandingColumn.default_value.label("value")).where(StandingColumn.stage_id == group.round_id)
            result = await db.execute(stmt)
            columns = result.mappings().all()

            column_values = [
                ColumnValues(user_id=user_id, column_id=col['id'], value=col['value'])
                for user_id in group.participants_ids
                for col in columns
            ]
            db.add_all(column_values)
            await db.commit()

            return {
                "message" : f"Group {group.name} created successfully"
            }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to create group")
    
    @staticmethod
    async def update_group(db: AsyncSession, group_update: GroupUpdate, group_id: UUID, stage_id: UUID):
        try:
            group = await extract_group_by_id(db=db, group_id=group_id)
            if not group:
                raise HTTPInternalServer(f"Group with id {group_id} not found")

            # Update name if provided
            if group_update.name:
                group.name = group_update.name

            # Update participants if provided
            if group_update.participants_ids is not None:
                result = await db.execute(select(GroupMembers.user_id).where(GroupMembers.group_id == group_id))
                group_member = result.scalars().all()
                add_members = list(set(group_update.participants_ids) - set(group_member))
                # Add new members
                new_members = [GroupMembers(group_id=group_id, user_id=user_id) 
                               for user_id in add_members]
                db.add_all(new_members)

                # Prepare column values
                stmt = select(StandingColumn.id.label("id"), StandingColumn.default_value.label("value")) \
                       .where(StandingColumn.stage_id == stage_id)
                result = await db.execute(stmt)
                columns = result.mappings().all()

                if columns:
                    column_values = [
                        ColumnValues(user_id=user_id, column_id=col['id'], value=col['value'])
                        for user_id in add_members
                        for col in columns
                    ]
                    db.add_all(column_values)

            await db.commit()
            return {"message": f"Group '{group.name}' updated successfully"}

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer(f"Failed to update group: {e}") from e 
        
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
            raise HTTPInternalServer(f"Failed to update group table data {e}")
        
    @staticmethod
    async def delete_group_member( db: AsyncSession, group_id :UUID, user_id : UUID, stage_id : UUID):
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
        stmt = select(StandingColumn.id).where(StandingColumn.stage_id == stage_id)
        result = await db.execute(stmt)
        column_ids = result.scalars().all()
        
        if column_ids:
            stmt = delete(ColumnValues).where(
                ColumnValues.column_id.in_(column_ids),
                ColumnValues.user_id == user_id
            )
            await db.execute(stmt)
        await db.commit()
        return {
            "message": f"Member {username} removed from group {group_name} successfully"
        }
    
    @staticmethod
    async def delete_group( db : AsyncSession,group_id : UUID):
        try:
            stmt = select(Group).where(Group.id == group_id).options(selectinload(Group.members))
            result = await db.execute(stmt)
            group = result.scalar_one_or_none()

            if not group:
                raise HTTPNotFound("Group not found")
            
            stmt = delete(Group).where(Group.id == group_id)
            await db.execute(stmt)

            stage_id = group.stage_id

            stmt = select(StandingColumn.id).where(StandingColumn.stage_id == stage_id)
            result = await db.execute(stmt)
            column_ids = result.scalars().all()

            user_ids  = [u.user_id for u in group.members]

            # Delete ColumnValues related to this group
            if column_ids and user_ids:
                stmt = delete(ColumnValues).where(
                    ColumnValues.column_id.in_(column_ids),
                    ColumnValues.user_id.in_(user_ids)
                )
                await db.execute(stmt)

            await db.commit()

            return {
                "message" : f"Group deleted successfully"
            }
        except SQLAlchemyError as e:
            raise HTTPInternalServer("Database error occur:", e)
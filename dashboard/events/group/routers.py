from fastapi import APIRouter, Depends, HTTPException, status
from events.group.schema import GroupDetail, GroupUpdate, AddGroupMember, GroupTableUpdate
from models import Group, GroupMembers, User,StandingColumn, ColumnValues, Stage, Event, Qualifier
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete, and_, func
from uuid import UUID
from db_connect import get_db_session
from sqlalchemy.exc import SQLAlchemyError
from events.group.service import GroupServices
from collections import defaultdict
from sqlalchemy.orm import selectinload
router = APIRouter()

@router.post("")
async def create_group(
    event_id : UUID,
    group: GroupDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    try:
        new_group = Group(
            stage_id=group.round_id,
            name=group.name,
            event_id= event_id
        )

        db.add(new_group)
        await db.flush()  # ensures new_group.id is available

        members = [
                GroupMembers(group_id=new_group.id, user_id=user_id)
                for user_id in group.participants_id
            ]
        db.add_all(members)

        await db.commit()

        return {
            "message": "Group added Successfully",
            "id": new_group.id,
            "members" : [user_id for user_id in group.participants_id]
        }
    except SQLAlchemyError as e:
        await db.rollback()
        return {
            "message": "Failed to add group",
            "error": str(e)
        }


@router.get("/info/{stage_id}")
async def extract_group_by_event(stage_id:UUID,db: Annotated[AsyncSession, Depends(get_db_session)]):
    stmt = select(Group.id,Group.name).where(Group.stage_id == stage_id)
    result = await db.execute(stmt)
    group_info = result.all()

    return [
        {
            "id" :  group.id,
            "groupname" : group.name
        }
        for group in group_info
    ]
    

@router.get("/event/{event_id}")
async def retrieve_group(db: Annotated[AsyncSession, Depends(get_db_session)],event_id : UUID):
    return await GroupServices.get_group_detail_in_event_services(db=db, event_id=event_id)


@router.patch("/{group_id}")
async def update_group(
    group_id: UUID,
    group_update: GroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    try:
        stmt = select(Group).where(Group.id == group_id)
        result = await db.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        if group_update.name is not None:
            group.name = group_update.name


        # Update participants if provided
        if group_update.participants_id is not None:
            # Delete existing members
            await db.execute(delete(GroupMembers).where(GroupMembers.group_id == group_id))
            
            # Add new members
            new_members = [
                GroupMembers(group_id=group_id, user_id=user_id)
                for user_id in group_update.participants_id
            ]
            db.add_all(new_members)

        await db.commit()

        return {
            "message": "Group updated successfully",
            "group_id": group.id,
        }

    except SQLAlchemyError as e:
        await db.rollback()
        return {"message": "Failed to update group", "error": str(e)}   
    
@router.delete("/{group_id}")
async def delete_group(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    stmt = select(Group).where(Group.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    stmt = delete(Group).where(Group.id == group_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Group {group.name} deleted successfully"
    }
    
@router.post("/player")
async def add_group_member(
    group_member_detail : AddGroupMember,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    new_group_member = GroupMembers(
        group_id = group_member_detail.group_id,
        user_id = group_member_detail.user_id
    )
    db.add(new_group_member)
    await db.commit()
    return{
        "message" : "Group Member added successfully",
        "id" : new_group_member.id
    }



@router.patch("/{group_id}/members")
async def update_group_table_data(
    group_id: UUID,
    table_update: GroupTableUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
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

                print("Existing value:",existing_value)
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
            "group_id": group_id
        }

    except SQLAlchemyError as e:
        await db.rollback()
        return {"message": "Failed to update group table data", "error": str(e)}
    

@router.delete("/member/{user_id}/group/{group_id}")
async def delete_group_member(
    user_id: UUID,
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
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
        raise HTTPException(status_code=404, detail="Group Member not found")

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



@router.get("/byround")
async def extract_group_by_round(
    round_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    stmt = select(Group.id, Group.name).where(Group.stage_id == round_id)
    result = await db.execute(stmt)
    group_info = result.mappings().all()

    return [
        {
            "id" : gi.id,
            "name" : gi.name
        }

        for gi in group_info
    ]

@router.get("/member")
async def extract_member_of_group(
    group_id : UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    stmt = (
        select(GroupMembers.user_id, User.username)
        .join(User, User.id == GroupMembers.user_id)
        .where(GroupMembers.group_id == group_id)
    )
    result = await db.execute(stmt)

    group_member = result.mappings().all()

    return [
        {
            "id" : gm.user_id,
            "username" : gm.username
        }

        for gm in group_member
    ]
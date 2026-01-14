from fastapi import APIRouter, Depends, HTTPException, status
from events.group.schema import GroupDetail, GroupUpdate, AddGroupMember
from models import Group, GroupMembers, User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session
from sqlalchemy.exc import SQLAlchemyError
router = APIRouter()

@router.post("")
async def create_group(
    group: GroupDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    try:
        new_group = Group(
            stage_id=group.stage_id,
            name=group.name
        )

        db.add(new_group)
        await db.flush()  # ensures new_group.id is available

        members = [
                GroupMembers(group_id=new_group.id, user_id=user_id)
                for user_id in group.user_id
            ]
        db.add_all(members)

        await db.commit()

        return {
            "message": "Group added Successfully",
            "id": new_group.id,
            "members" : [user_id for user_id in group.user_id]
        }
    except SQLAlchemyError as e:
        await db.rollback()
        return {
            "message": "Failed to add group",
            "error": str(e)
        }


@router.get("")
async def retrieve_group(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    group_id: UUID | None = None,
):
    try:
        stmt = select(
            Group.id.label("group_id"),
            Group.name.label("group_name"),
            User.id.label("user_id"),
            User.username.label("username")
        ).join(
            GroupMembers, Group.id == GroupMembers.group_id
        ).join(
            User, GroupMembers.user_id == User.id
        )

        if group_id:
            stmt = stmt.where(Group.id == group_id)

        result = await db.execute(stmt)
        rows = result.all()

        # Convert to structured response
        group_dict = {}
        for row in rows:
            gid = row.group_id
            if gid not in group_dict:
                group_dict[gid] = {
                    "group_id": row.group_id,
                    "group_name": row.group_name,
                    "members": []
                }
            group_dict[gid]["members"].append({
                "user_id": row.user_id,
                "username": row.username
            })

        return list(group_dict.values())

    except Exception as e:
        return {"message": "Failed to retrieve groups", "error": str(e)}
    
@router.put("/{group_id}")
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
        if group_update.stage_id is not None:
            group.stage_id = group_update.stage_id

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
        "message" : f"Group {group_id} deleted successfully"
    }
    
@router.post("")
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


@router.delete("/{groupmember_id}")
async def delete_group_member(
    groupmember_id : UUID, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    stmt = select(GroupMembers).where(GroupMembers.id == groupmember_id )
    result = await db.execute(stmt)
    groupmember = result.scalar_one_or_none()

    if not groupmember:
        raise HTTPException(status_code=404, detail="Group Member not found")
    
    stmt = delete(GroupMembers).where(GroupMembers.id == groupmember_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Group {groupmember_id} deleted successfully"
    }
    
from fastapi import APIRouter, Depends
from events.group.schema import GroupDetail, GroupUpdate, AddGroupMember, GroupTableUpdate, GroupEvent, GroupByRound, GroupMember
from models import Group, GroupMembers, User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session
from events.group.service import GroupServices
from events.group.crud import extract_group_by_id

router = APIRouter()

@router.post("")
async def create_group(
    event_id : UUID,
    group: GroupDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    await GroupServices.create_group(db=db, group=group, event_id=event_id)


@router.get("/info/{stage_id}")
async def extract_group_by_event(stage_id:UUID,db: Annotated[AsyncSession, Depends(get_db_session)]):
    stmt = select(Group.id,Group.name.label("groupname")).where(Group.stage_id == stage_id)
    result = await db.execute(stmt)
    group_info = result.all()

    return [GroupEvent.model_validate(gi) for gi in group_info]
    

@router.get("/event/{event_id}")
async def retrieve_group(db: Annotated[AsyncSession, Depends(get_db_session)],event_id : UUID):
    return await GroupServices.get_group_detail_in_event_services(db=db, event_id=event_id)


@router.patch("/{group_id}")
async def update_group(
    group_id: UUID,
    group_update: GroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    return await GroupServices.update_group(db=db, group_update=group_update, group_id=group_id) 
    
@router.delete("/{group_id}")
async def delete_group(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    await extract_group_by_id(db=db, group_id=group_id)
    
    stmt = delete(Group).where(Group.id == group_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Group deleted successfully"
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
    }



@router.patch("/{group_id}/members")
async def update_group_table_data(
    group_id: UUID,
    table_update: GroupTableUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    return await GroupServices.update_group_table_data(db=db, table_update=table_update, group_id=group_id)
    

@router.delete("/member/{user_id}/group/{group_id}")
async def delete_group_member(
    user_id: UUID,
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    return await GroupServices.delete_group_member(db=db, user_id=user_id, group_id=group_id)


@router.get("/byround")
async def extract_group_by_round(
    round_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    stmt = select(Group.id, Group.name).where(Group.stage_id == round_id)
    result = await db.execute(stmt)
    group_info = result.mappings().all()

    return [GroupByRound.model_validate(gi) for gi in group_info]

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

    return [GroupMember.model_validate(gm) for gm in group_member]
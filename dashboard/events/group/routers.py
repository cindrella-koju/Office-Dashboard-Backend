from fastapi import APIRouter, Depends, HTTPException, status
from events.group.schema import GroupDetail, GroupUpdate, AddGroupMember, GroupTableUpdate
from models import Group, GroupMembers, User,StandingColumn, ColumnValues, Stage, Event
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete, and_
from uuid import UUID
from db_connect import get_db_session
from sqlalchemy.exc import SQLAlchemyError
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

# @router.get("")
# async def retrieve_group(
#     db: Annotated[AsyncSession, Depends(get_db_session)],
#     group_id: UUID | None = None,
# ):
#     try:
#         gm = GroupMembers
#         g = Group
#         u = User
#         sc = StandingColumn
#         cv = ColumnValues
#         s = Stage
#         stmt = (
#             select(
#                 g.id.label("group_id"),
#                 g.name.label("group_name"),
#                 g.stage_id.label("stage_id"),
#                 s.name.label("stage_name"),
#                 u.id.label("user_id"),
#                 u.username.label("username"),
#                 sc.id.label("column_id"),
#                 sc.column_field,
#                 cv.value
#             )
#             .join(gm, g.id == gm.group_id)
#             .join(u, gm.user_id == u.id)
#             .join(sc, sc.stage_id == g.stage_id)  # all columns for the group's stage
#             .outerjoin(cv, (cv.user_id == u.id) & (cv.column_id == sc.id))  # LEFT JOIN for values
#         )

#         if group_id:
#             stmt = stmt.where(g.id == group_id)

#         result = await db.execute(stmt)
#         rows = result.all()


#         # group_dict = {}
#         # for row in rows:
#         #     sid = row.stage_id
#         #     if sid not in group_dict:
#         #         group_dict[sid] = {
#         #             "stage_id": row.stage_id,
#         #             "stage_name" : row.stage_name,
#         #             "groups" : {}
#         #         }

#         #     gid = row.group_id
#         #     if gid not in group_dict[sid]["groups"]:
#         #         group_dict[sid]["groups"][gid] = {
#         #             "group_id": row.group_id,
#         #             "group_name": row.group_name,
#         #             "members": {}
#         #         }

#         #     uid = row.user_id
#         #     if uid not in group_dict[sid]["groups"][gid]["members"]:
#         #         group_dict[sid]["groups"][gid]["members"][uid] = {
#         #             "user_id": row.user_id,
#         #             "username": row.username,
#         #             "columns": []
#         #         }

#         #     group_dict[sid]["groups"][gid]["members"][uid]["columns"].append({
#         #         "column_id": row.column_id,
#         #         "column_field": row.column_field,
#         #         "value": row.value
#         #     })

#         # for gdata in group_dict.values():
#         #     gdata["groups"] = list(gdata["groups"].values())
#         #     for group in gdata["groups"]:
#         #         group["members"] = list(group["members"].values())

#         # return list(group_dict.values())

#         return [
#             {
#                 "round_name" : r.stage_name,
#                 "id" : r.stage_id
#             }
#             for r in rows
#         ]

#     except Exception as e:
#         return {"message": "Failed to retrieve groups", "error": str(e)}
    

@router.get("/event/{event_id}")
async def retrieve_group(db: Annotated[AsyncSession, Depends(get_db_session)],event_id : UUID):
    
    query = (
        select(
            User.username.label("username"),
            GroupMembers.user_id,
            Stage.id.label("stage_id"),
            Stage.name.label("stage_name"),
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
    rows = result.mappings().all()

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

            # print("User Id:",uid)
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
    # return [{
    #     "username":s.username,
    #     "user_id" : s.user_id,
    #     "stage_name" : s.stage_name,
    #     "stage_id" : s.stage_id,
    #     "group_id" : s.group_id,
    #     "group_name" : s.group_name,
    #     "column_name" : s.column_name,
    #     "column_id" : s.column_id,
    #     "column_value" : s.column_value
    # }

    #     for s in rows
    # ]

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
        if group_update.stage_id is not None:
            group.stage_id = group_update.stage_id

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
        "message" : f"Group {group_id} deleted successfully"
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
    stmt = select(GroupMembers).where(
        GroupMembers.user_id == user_id,
        GroupMembers.group_id == group_id
    )
    result = await db.execute(stmt)
    groupmember = result.scalar_one_or_none()

    if not groupmember:
        raise HTTPException(status_code=404, detail="Group Member not found")
    
    stmt = delete(GroupMembers).where(
        GroupMembers.user_id == user_id,
        GroupMembers.group_id == group_id
    )
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Member {user_id} removed from group {group_id} successfully"
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
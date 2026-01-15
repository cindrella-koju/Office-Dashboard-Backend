from fastapi import APIRouter, Depends, HTTPException, status
from events.stage.schema import StageDetail, EditStageDetail, StageResponse
from models import Stage, user_event_association, User, GroupMembers
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import select, delete
from uuid import UUID
from db_connect import get_db_session

router = APIRouter()

@router.post("")
async def create_stage(stage : StageDetail,  db : Annotated[AsyncSession,Depends(get_db_session)]):
    new_state = Stage(
        event_id = stage.event_id,
        name = stage.name,
        round_order = stage.round_order
    )

    db.add(new_state)
    await db.commit()
    return{
        "message" : "Stage added successfully",
        "id" : new_state.id
    }

@router.patch("")
async def edit_stage(
    stage_detail: EditStageDetail,
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID | None = None,
):
    result = await db.execute(select(Stage).where(Stage.id == stage_id))
    stage = result.scalars().first()

    if not stage:
        raise HTTPException(
            detail="Stage not found",
            status_code= status.HTTP_404_NOT_FOUND
        )
    
    if stage_detail.name:
        stage.name = stage_detail.name

    if stage_detail.round_order:
        stage.round_order = stage_detail.round_order

    await db.commit()

    return {
        "message" : "Stage Aded Successfully",
        "stage_id" : stage_id
    }

@router.get("")
async def retrieve_stage(
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID | None = None,
):
    if stage_id:
        result = await db.execute(select(Stage).where(Stage.id == stage_id))
        stage = result.scalars().first()
        if not stage:
            raise HTTPException(
                detail="Stage not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return StageResponse(**stage.__dict__)
    else:
        result = await db.execute(select(Stage))
        stages = result.scalars().all()
        if not stages:
            raise HTTPException(
                detail="Stage not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return [StageResponse(**stage.__dict__) for stage in stages]
    
@router.delete("")
async def delete_stage(
    db: Annotated[AsyncSession,Depends(get_db_session)],
    stage_id: UUID | None = None,
):
    result = await db.execute(select(Stage).where(Stage.id == stage_id))
    stage = result.scalars().first()
    if not stage:
        raise HTTPException(
            detail="Stage not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    stmt = delete(Stage).where(Stage.id == stage_id)
    await db.execute(stmt)
    await db.commit()

    return {
        "message" : f"Stage {stage_id} deleted successfully"
    }


from pydantic import BaseModel,ConfigDict
from typing import List

class RoundInfo(BaseModel):
    id : UUID
    name :  str

    model_config = ConfigDict(from_attributes=True)
    
class CreateGroupResponse(BaseModel):
    round : List[RoundInfo]
    group_name : str
    participants : List[UserResponse]

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id : UUID
    username : str

    model_config = ConfigDict(from_attributes=True)

@router.get("/creategroup")
async def createeeee(db: Annotated[AsyncSession,Depends(get_db_session)], event_id : UUID): 
    stmt = select(Stage).where(Stage.event_id == event_id)
    result = await db.execute(stmt)
    stages = result.scalars().all()

    stageinfo = [RoundInfo.from_orm(stage) for stage in stages]

    participants = await extract_participants(event_id=event_id, db=db)

    return CreateGroupResponse(
        round=stageinfo,
        group_name="string",
        participants=participants
    )



async def extract_participants(event_id: UUID, db: AsyncSession):
    stmt = (
        select(User)
        .join(user_event_association, User.id == user_event_association.c.user_id)
        .where(user_event_association.c.event_id == event_id)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    return [UserResponse.from_orm(user) for user in users]

@router.get("/changegroupmember")
async def change_group_members(event_id: UUID, db: Annotated[AsyncSession,Depends(get_db_session)],group_id : UUID):
    participants = await extract_participants(event_id=event_id, db=db)
    gm = GroupMembers
    u = User
    stmt = select(
        gm.user_id,
        u.username
    ).join(gm,gm.user_id == u.id).where(gm.group_id == group_id)
    result = await db.execute(stmt)
    group_members = result.all()

    print("Results:",result)
    return{
        "participants": participants,
        "group_members" : [
            {
                "id" : user.user_id,
                "username" : user.username
            }
            for user in group_members
        ]
    }
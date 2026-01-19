from models import user_event_association, User, Event, GroupMembers, Event, Stage, Group, StandingColumn, ColumnValues, Qualifier
from fastapi import APIRouter, Depends, HTTPException, status
from participants.schema import Participants, ParticipantsUserResponse, ParticipantsEventResponse, UserResponse
from db_connect import get_db_session
from dependencies import get_current_user
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from users.schema import RoleEnum
from sqlalchemy import insert, select, exists
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

@router.post("")
async def create_participants(
    participant: Participants,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    try:
        # 1. Insert participant into association table
        stmt = insert(user_event_association).values(
            user_id=participant.user_id,
            event_id=participant.event_id,
            is_winner=False,
        )

        # 2. Get stage_id for round 1
        result = await db.execute(
            select(Stage.id).where(
                Stage.event_id == participant.event_id,
                Stage.round_order == 1
            )
        )
        stage_id = result.scalar_one_or_none()

        if not stage_id:
            raise HTTPException(
                status_code=404,
                detail="Stage round 1 not found for this event"
            )

        # 3. Get standing columns with default values
        result = await db.execute(
            select(
                StandingColumn.id,
                StandingColumn.default_value
            ).where(StandingColumn.stage_id == stage_id)
        )

        cols_and_vals = result.all()

        # 4. Create ColumnValues records
        new_col_vals = [
            ColumnValues(
                user_id=participant.user_id,
                column_id=col_id,
                value=default_value
            )
            for col_id, default_value in cols_and_vals
        ]
        
        #Add in Round 1 Qualifier
        new_qulifier = Qualifier(
            event_id = participant.event_id,
            stage_id = stage_id,
            user_id = participant.user_id
        )
        # 5. Execute all in one transaction
        await db.execute(stmt)
        db.add_all(new_col_vals)
        db.add(new_qulifier)
        await db.commit()

        return {"message": "Participant added successfully"}

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add participant: {str(e)}"
        )



@router.get("/event")
async def extract_participant_by_event(
    event_id : UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != RoleEnum.superadmin and current_user["role"] != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    stmt = (
        select(
            user_event_association.c.user_id,
            user_event_association.c.event_id,
            user_event_association.c.is_winner,
            User.username,
        )
        .join(User, User.id == user_event_association.c.user_id)
        .where(user_event_association.c.event_id == event_id)
    )

    result = await db.execute(stmt)
    participants = result.mappings().all()

    return [ParticipantsEventResponse(**p) for p in participants]

@router.get("/user")
async def extract_participant_by_event(
    user_id : UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != RoleEnum.superadmin and current_user["role"] != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    stmt = (
        select(
            user_event_association.c.user_id,
            user_event_association.c.event_id,
            user_event_association.c.is_winner,
            User.username,
            Event.title
        )
        .join(User, User.id == user_event_association.c.user_id)
        .join(Event, Event.id == user_event_association.c.event_id)
        .where(user_event_association.c.event_id == user_id)
    )

    result = await db.execute(stmt)
    participants = result.mappings().all()

    return [ParticipantsUserResponse(**p) for p in participants]

    
# from sqlalchemy import select

# stmt = select(user_event_association).where(
#     user_event_association.c.event_id == event.id,
#     user_event_association.c.is_winner == True
# )

# winners = session.execute(stmt).all()

async def extract_participants(event_id: UUID, db: AsyncSession):
    stmt = (
        select(User)
        .join(user_event_association, User.id == user_event_association.c.user_id)
        .where(user_event_association.c.event_id == event_id)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    return [UserResponse.from_orm(user) for user in users]

@router.get("")
async def retrieve_participants(event_id: UUID, db: Annotated[AsyncSession,Depends(get_db_session)]):
    participants = await extract_participants(event_id=event_id, db=db)

    return{
        "participants" : participants
    }

@router.get("/not-in-group")
async def participants_not_in_group(event_id: UUID, db: Annotated[AsyncSession,Depends(get_db_session)], group_id : UUID | None = None):
    if group_id:
        result = await db.execute(
            select(GroupMembers.user_id, User.username)
            .join(User, User.id == GroupMembers.user_id)
            .where(GroupMembers.group_id == group_id)
        )

        users = result.all()

        user_in_group = [
            {
                "id": row.user_id,
                "username": row.username
            }
            for row in users
        ]
    
    subq = (
        select(GroupMembers.user_id)
        .join(Group)
        .join(Stage)
        .where(Stage.event_id == event_id)
    )


    stmt = (
        select(User.id,User.username)
        .join(user_event_association, User.id == user_event_association.c.user_id)
        .where(user_event_association.c.event_id == event_id)
        .where(~User.id.in_(subq))
    )

    result = await db.execute(stmt)
    users = result.all()

    participants = [
        {"id": u[0], "username": u[1]} for u in users
    ]

    if group_id:
        participants = participants + user_in_group

    return {
        "participants" : participants
    }


# @router.get("/not-in-group")
# async def participants_not_in_group(
#     event_id: UUID,
#     db: Annotated[AsyncSession, Depends(get_db_session)]
# ):
#     ep = user_event_association
#     gm = GroupMembers
#     g = Group
#     s = Stage
#     u = User

#     subquery = (
#         select(1)
#         .select_from(gm)
#         .join(g, g.id == gm.group_id)
#         .join(s, s.id == g.stage_id)
#         .where(
#             gm.user_id == ep.c.user_id,
#             s.event_id == event_id
#         )
#     )
    

#     stmt = (
#         select(
#             u.id,
#             u.username
#         )
#         .join(ep, ep.c.user_id == u.id)
#         .where(
#             ep.c.event_id == event_id,
#             ~exists(subquery)
#         )
#     )

#     result = await db.execute(stmt)

#     return [
#         {"id": user.id, "username": user.username}
#         for user in result.all()
#     ]
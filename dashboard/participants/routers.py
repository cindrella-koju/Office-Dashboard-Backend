from models import user_event_association, User, Event, GroupMembers, Event, Stage, Group, StandingColumn, ColumnValues, Qualifier
from fastapi import APIRouter, Depends, HTTPException, status
from participants.schema import Participants, ParticipantsUserResponse, ParticipantsEventResponse, UserResponse
from db_connect import get_db_session
from dependencies import get_current_user
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from users.schema import RoleEnum
from sqlalchemy import insert, select,and_, outerjoin
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

@router.post("")
async def create_participants(
    event_id: UUID,
    participants: Participants,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    try:
        # 1. Insert into user_event_association (bulk)
        association_rows = [
            {
                "user_id": p,
                "event_id": event_id,
                "is_winner": False,
            }
            for p in participants.user_id
        ]

        await db.execute(
            insert(user_event_association),
            association_rows
        )

        # 2. Get stage_id for round 1
        result = await db.execute(
            select(Stage.id).where(
                Stage.event_id == event_id,
                Stage.round_order == 1
            )
        )
        stage_id = result.scalar_one_or_none()

        if not stage_id:
            raise HTTPException(
                status_code=404,
                detail="Stage round 1 not found for this event"
            )

        # 3. Get standing columns + default values
        result = await db.execute(
            select(
                StandingColumn.id,
                StandingColumn.default_value
            ).where(StandingColumn.stage_id == stage_id)
        )
        cols_and_vals = result.all()

        # 4. Create ColumnValues for each user & column
        new_col_vals = [
            ColumnValues(
                user_id=p,
                column_id=col_id,
                value=default_value
            )
            for p in participants.user_id
            for col_id, default_value in cols_and_vals
        ]

        # 5. Create Round 1 qualifiers
        new_qualifiers = [
            Qualifier(
                event_id=event_id,
                stage_id=stage_id,
                user_id=p
            )
            for p in participants.user_id
        ]

        db.add_all(new_col_vals)
        db.add_all(new_qualifiers)

        await db.commit()

        return {"message": "Participants added successfully"}

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add participants: {str(e)}"
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

@router.get("/not-participants")
async def retrieve_not_participants(event_id : UUID,  db: Annotated[AsyncSession,Depends(get_db_session)]):
    participants = await extract_participants(event_id=event_id, db=db)
    participant_ids = [p.id for p in participants]

    stmt = select(User.id,User.username).where(User.id.notin_(participant_ids))
    result = await db.execute(stmt)  
    users = result.all()
    return [
        {
            "id" : user.id,
            "username" : user.username
        }
        for user in users
    ]

@router.get("/not_qualifier")
async def retrieve_user_not_in_qualifier(stage_id : UUID,event_id : UUID,db: Annotated[AsyncSession,Depends(get_db_session)]):
    p = user_event_association
    u = User
    q = Qualifier
    stmt = (select(u.id,u.username)
            .join(p,p.c.user_id == u.id)
            .outerjoin(
                Qualifier,
                and_(
                    p.c.user_id == Qualifier.user_id,
                    p.c.event_id == Qualifier.event_id,
                    Qualifier.stage_id == stage_id
                )
            ).where(and_(Qualifier.id == None,p.c.event_id == event_id)))
    result = await db.execute(stmt)
    users = result.all()

    print("Users:",users)
    return [
        {
            "user_id" : q.id,
            "username" : q.username
        }
        for q in users
    ]


# @router.get("/not-in-group")
# async def participants_not_in_group(event_id: UUID,stage_id : UUID, db: Annotated[AsyncSession,Depends(get_db_session)], group_id : UUID | None = None):
#     if group_id:
#         result = await db.execute(
#             select(GroupMembers.user_id, User.username)
#             .join(User, User.id == GroupMembers.user_id)
#             .where(GroupMembers.group_id == group_id)
#         )

#         users = result.all()

#         user_in_group = [
#             {
#                 "id": row.user_id,
#                 "username": row.username
#             }
#             for row in users
#         ]
    
#     subq = (
#         select(GroupMembers.user_id)
#         .join(Group)
#         .join(Stage)
#         .where(
#             and_(
#                 Stage.event_id == event_id,
#                 Stage.id == stage_id
#             )
#         )
#     )


#     stmt = (
#         select(User.id,User.username)
#         .join(user_event_association, User.id == user_event_association.c.user_id)
#         .where(user_event_association.c.event_id == event_id)
#         .where(~User.id.in_(subq))
#     )

#     result = await db.execute(stmt)
#     users = result.all()

#     participants = [
#         {"id": u[0], "username": u[1]} for u in users
#     ]

#     if group_id:
#         participants = participants + user_in_group

#     return {
#         "participants" : participants
#     }


@router.get("/not-in-group/event/{event_id}/stage/{stage_id}")
async def participants_not_in_group(event_id : UUID, stage_id:UUID, db: Annotated[AsyncSession,Depends(get_db_session)]):
    

    subq = (select(GroupMembers.user_id)
        .join(Group)
        .join(Stage)
        .where(
        and_(
                Group.stage_id == stage_id,
                Stage.event_id == event_id,
            )
        )
    ).subquery()
    
    stmt2 = select(User.id,User.username).join(Qualifier).where(
        and_(
            Qualifier.event_id == event_id ,
            Qualifier.stage_id == stage_id,
            Qualifier.user_id.not_in(subq)
        )
    )

    group_result = await db.execute(stmt2)
    group_member = group_result.all()
    return [
        {
            "id" : p.id,
            "username" : p.username
        }
        for p in group_member
    ]


# [
#   {
#     "id": "c397aa12-2214-4796-a1d0-4d1dc8c28974"
#   },
#   {
#     "id": "04d36c46-d7c1-4e06-8250-cdfd4bbb80f3"
#   },
#   {
#     "id": "8f9f0c0f-d3a2-4181-a6f0-7ba5813f4cb6"
#   },
#   {
#     "id": "a8958723-f998-48ea-b7c1-92647c874e98"
#   },
#   {
#     "id": "06ffbc8a-9bca-4979-bbc9-3477e0800eef"
#   },
#   {
#     "id": "c68eae35-907d-4998-9f3d-b9a20b1ed937"
#   }
# ]


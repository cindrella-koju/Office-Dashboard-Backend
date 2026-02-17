from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID
from events.stage.crud import extract_stage_by_id
from events.group.service import GroupServices
from models import GroupMembers, Group, Stage, User, Qualifier, user_event_association
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from events.crud import extract_event_by_id
from exception import HTTPNotFound

class ParticipantsServices:
    @staticmethod
    async def validate_participants(
        db:AsyncSession,
        user_id: UUID,
        event_id : UUID
    ):
        result = await db.execute(
            select(user_event_association)
            .where(
                and_(
                    user_event_association.c.user_id == user_id,
                    user_event_association.c.event_id == event_id
                )
            ))
        participants = result.scalar_one_or_none()

        if not participants:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Round not found"
            )
        
    @staticmethod
    async def extract_participants_username(db=AsyncSession, event_id = UUID, user_id = UUID):
        await ParticipantsServices.validate_participants(db=db, event_id=event_id, user_id=user_id)

        stmt = (
            select(User.username)
            .join(
                user_event_association,
                User.id == user_event_association.c.user_id
            )
            .where(
                and_(
                    user_event_association.c.user_id == user_id,
                    user_event_association.c.event_id == event_id
                )
            )
        )

        result = await db.execute(stmt)
        username = result.scalar_one_or_none()

        return username
    
    @staticmethod
    async def get_participants_not_in_group( 
        db : AsyncSession, 
        event_id : UUID ,
        stage_id : UUID,
        group_id : UUID | None = None
    ):
        event = await extract_event_by_id( db=db, event_id=event_id)
        if not event:
            HTTPNotFound("Event not found")
        await extract_stage_by_id(db = db, stage_id=stage_id)

        if group_id:
            await GroupServices.validate_group(db = db, group_id=group_id)

        # Extract the user already in group
        subq = (select(GroupMembers.user_id)
            .join(Group)
            .join(Stage)
            .where(
            and_(
                    Group.stage_id == stage_id,
                    Stage.event_id == event_id,
                )
            )
        )

        # Get qualified user who is not in group
        qualifier_result = await db.execute(select(User.id,User.username).join(Qualifier).where(
            and_(
                Qualifier.event_id == event_id ,
                Qualifier.stage_id == stage_id,
                Qualifier.user_id.not_in(subq)
            )
        ).order_by(User.created_at))
        participants = qualifier_result.mappings().all()

        # If editing then include user already in group as well
        if group_id:
            group_result = await db.execute(
                select(GroupMembers.user_id.label("id"), User.username.label("username"))
                .join(User, User.id == GroupMembers.user_id)
                .where(GroupMembers.group_id == group_id)
            )
            group_users = group_result.mappings().all()
            participants.extend(group_users)
        
        # Remove duplicates
        participants = list({p["id"]: p for p in participants}.values())

        return participants
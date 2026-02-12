from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID
from events.stage.services import StageServices
from events.group.service import GroupServices
from events.services import EventServices
from models import GroupMembers, Group, Stage, User, Qualifier
from sqlalchemy import select, and_

class ParticipantsServices:
    @staticmethod
    async def get_participants_not_in_group( 
        db : AsyncSession, 
        event_id : UUID ,
        stage_id : UUID,
        group_id : UUID | None = None
    ):
        await EventServices.validate_event(db=db, event_id=event_id)
        await StageServices.validate_stage(db = db, stage_id=stage_id)

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
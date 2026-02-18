from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import user_event_association, User
from sqlalchemy import select,and_
from participants.schema import UserResponse
from exception import HTTPNotFound

async def extract_participants(event_id: UUID, db: AsyncSession):
    stmt = (
        select(User)
        .join(user_event_association, User.id == user_event_association.c.user_id)
        .where(user_event_association.c.event_id == event_id)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    if not stmt:
        raise HTTPNotFound("Participant of this event not found")
    return [UserResponse.model_validate(user) for user in users]

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
            raise HTTPNotFound("Round not found")
        return participants
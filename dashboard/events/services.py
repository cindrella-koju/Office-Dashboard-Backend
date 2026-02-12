from sqlalchemy.ext.asyncio import AsyncSession
from models import Event, Stage, StandingColumn
from uuid import UUID
from sqlalchemy import select
from events.schema import StatusEnum
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

async def extract_all_event(db: AsyncSession, status: str | None = None):
    stmt = select(Event).order_by(Event.created_at)
    if status and status.lower() != "all":
        stmt = stmt.where(Event.status == status.lower())

    result = await db.execute(stmt)
    events = result.scalars().all()
    return events

async def extract_one_event(db:AsyncSession, event_id : UUID):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    return event

async def create_event(db: AsyncSession, event):
    new_event = Event(
        title=event.title,
        description=event.description or "",
        startdate=event.startdate,
        enddate=event.enddate,
        status=StatusEnum(event.status),
        progress_note=event.progress_note or "",
    )

    db.add(new_event)
    await db.flush() 

    return new_event


async def create_default_round(db: AsyncSession, new_event: Event):
    new_round = Stage(
        event_id=new_event.id,
        name="Round 1",
        round_order=1
    )

    db.add(new_round)
    await db.flush()

    return new_round


async def create_default_standing_col(db: AsyncSession, new_round: Stage):
    default_standing_col = [
        {"column_field": "Match Played", "default_value": "0"},
        {"column_field": "Win", "default_value": "0"},
        {"column_field": "Loss", "default_value": "0"},
        {"column_field": "Draw", "default_value": "0"},
        {"column_field": "Points", "default_value": "0"},
    ]

    new_standing_columns = [
        StandingColumn(
            stage_id=new_round.id,
            column_field=col["column_field"],
            default_value=col["default_value"]
        )
        for col in default_standing_col
    ]

    db.add_all(new_standing_columns)


async def create_event_services(db: AsyncSession, event):
    try:
        new_event = await create_event(db, event)
        new_round = await create_default_round(db, new_event)
        await create_default_standing_col(db, new_round)

        await db.commit()

        return {
            "message": "Event added successfully",
        }

    except SQLAlchemyError as e:
        await db.rollback()
        return {
            "message": "Failed to add Event",
            "error": str(e)
        }


class EventServices:
    @staticmethod
    async def validate_event(
        db: AsyncSession,
        event_id: UUID,
    ):
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
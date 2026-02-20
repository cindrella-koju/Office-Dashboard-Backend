from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID
from events.stage.crud import extract_stage_by_id
from events.group.service import GroupServices
from models import GroupMembers, Group, Stage, User, Qualifier, user_event_association, StandingColumn, ColumnValues, UserRole, Event
from sqlalchemy import select, and_, insert, delete
from events.crud import extract_event_by_id
from participants.crud import validate_participants
from exception import HTTPNotFound, HTTPInternalServer
from participants.schema import Participants, ParticipantsEventResponse, ParticipantsUserResponse, ParticipantsNotInGroup
from roles.services import get_member_role_id
from sqlalchemy.exc import SQLAlchemyError

class ParticipantsServices:        
    @staticmethod
    async def extract_participants_username(db=AsyncSession, event_id = UUID, user_id = UUID):
        await validate_participants(db=db, event_id=event_id, user_id=user_id)

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

        return [ParticipantsNotInGroup.model_validate(p) for p in participants]
    
    @staticmethod
    async def create_participants( db:AsyncSession, event_id : UUID, participants : Participants):
        try:
            # 1. Insert into user_event_association (bulk)
            association_rows = [
                {
                    "user_id": p,
                    "event_id": event_id,
                }
                for p in participants.user_id
            ]

            await db.execute(
                insert(user_event_association),
                association_rows
            )

            print("Working 1")
            # 2. Get stage_id for round 1
            result = await db.execute(
                select(Stage.id).where(
                    Stage.event_id == event_id,
                ).order_by(Stage.created_at)
            )
            stage_id = result.scalars().all()

            if not stage_id:
                raise HTTPNotFound("Stage round 1 not found for this event")

            print("Working 2")
            # 3. Get standing columns + default values
            result = await db.execute(
                select(
                    StandingColumn.id,
                    StandingColumn.default_value
                ).where(StandingColumn.stage_id == stage_id[0])
            )
            cols_and_vals = result.all()
            
            print("Working 3")
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
            
            print("Working 4")
            # 5. Create Round 1 qualifiers
            new_qualifiers = [
                Qualifier(
                    event_id=event_id,
                    stage_id=stage_id[0],
                    user_id=p
                )
                for p in participants.user_id
            ]

            db.add_all(new_col_vals)
            db.add_all(new_qualifiers)

            role_id = await get_member_role_id(db=db)
            userrole = [
                UserRole(
                    user_id = p,
                    event_id = event_id,
                    role_id = role_id
                )
                for p in participants.user_id
            ]
            db.add_all(userrole)
            await db.commit()

            return {"message": "Participants added successfully"}

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer(f"Failed to add participants: {str(e)}")

    @staticmethod
    async def extract_participant_by_event(db:AsyncSession, event_id : UUID):
        try:
            stmt = (
                select(
                    user_event_association.c.user_id,
                    user_event_association.c.event_id,
                    User.username,
                )
                .join(User, User.id == user_event_association.c.user_id)
                .where(user_event_association.c.event_id == event_id)
            )

            result = await db.execute(stmt)
            participants = result.mappings().all()

            return [ParticipantsEventResponse.model_validate(p) for p in participants]
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer(f"Failed to extract participants by event: {str(e)}")
        
    @staticmethod
    async def extract_participant_by_event_with_user(db : AsyncSession, user_id : UUID):
        try:
            stmt = (
                select(
                    user_event_association.c.user_id,
                    user_event_association.c.event_id,
                    User.username,
                    Event.title
                )
                .join(User, User.id == user_event_association.c.user_id)
                .join(Event, Event.id == user_event_association.c.event_id)
                .where(user_event_association.c.event_id == user_id)
            )

            result = await db.execute(stmt)
            participants = result.mappings().all()

            return [ParticipantsUserResponse.model_validate(p) for p in participants]
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer(f"Failed to extract participants by event with user: {str(e)}")
        
    @staticmethod
    async def delete_participants(db : AsyncSession, user_id : UUID, event_id : UUID):
        username = await ParticipantsServices.extract_participants_username(db = db, user_id=user_id, event_id=event_id)
        try:
            # Delete Participants
            stmt = delete(user_event_association).where(
                and_(
                    user_event_association.c.user_id == user_id,
                    user_event_association.c.event_id == event_id
                )
            )

            # Delete Qualifier
            stmt2 = delete(Qualifier).where(
                and_(
                    Qualifier.event_id == event_id,
                    Qualifier.user_id == user_id
                )
            )

            # Delete the role of User 
            stmt3 = delete(UserRole).where(
                and_(
                    UserRole.event_id == event_id,
                    UserRole.user_id == user_id
                )
            )
            await db.execute(stmt)
            await db.execute(stmt2)
            await db.execute(stmt3)
            await db.commit()

            return{
                "message" : f"Participants {username} deleted successfully"
            }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer(f"An error occured:{str(e)}")
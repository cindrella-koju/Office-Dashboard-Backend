from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import Qualifier, User, StandingColumn, ColumnValues, Stage
from sqlalchemy import select
from events.qualifier.crud import extract_qualifier_by_id
from events.qualifier.schema import QualifierModel
from sqlalchemy.exc import SQLAlchemyError
from exception import HTTPInternalServer, HTTPNotFound

class QualifierService:

    @staticmethod
    async def extract_username_from_qualifier_id(
        db : AsyncSession,
        qualifier_id : UUID
    ):
        await extract_qualifier_by_id(db = db,qualifier_id=qualifier_id)
        result = await db.execute(
            select(User.username).join(Qualifier,Qualifier.user_id == User.id).where(Qualifier.id == qualifier_id)
        )
        qualified_user = result.scalar_one_or_none()
        if not qualified_user:
            raise HTTPNotFound("Qualified user not found")
        return qualified_user
    
    @staticmethod
    async def create_qualifier(
        db: AsyncSession,
        qualifier : QualifierModel,
        event_id : UUID,
        stage_id : UUID
    ):
        try:
            # 1. Create new Qualifiers for each user
            new_qualifiers = [
                Qualifier(
                    event_id=event_id,
                    user_id=user_id,
                    stage_id=stage_id
                )
                for user_id in qualifier.user_id
            ]

            db.add_all(new_qualifiers)
            await db.commit()

            # 2. Fetch the columns and their default values for the given stage
            result = await db.execute(
                select(
                    StandingColumn.id,
                    StandingColumn.default_value
                ).where(StandingColumn.stage_id == stage_id)
            )
            cols_and_vals = result.all()

            # 3. Create ColumnValues for each user & column
            new_column_values = [
                ColumnValues(
                    user_id=user_id,
                    column_id=col_id,
                    value=default_value
                )
                for user_id in qualifier.user_id
                for col_id, default_value in cols_and_vals
            ]

            db.add_all(new_column_values)
            await db.commit()

            return {"message": "Qualifier created successfully"}

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer(f"An error occurred: {str(e)}")
        
    @staticmethod
    async def retrieve_qualifier_by_event(db : AsyncSession, event_id : UUID):
        stmt = (
            select(
                Qualifier.id.label("qualifier_id"),
                User.id.label("user_id"),
                User.email,
                User.username,
                Stage.name.label("round_name"),
            )
            .select_from(Qualifier)
            .join(User, User.id == Qualifier.user_id)
            .join(Stage, Stage.id == Qualifier.stage_id)
            .where(Qualifier.event_id == event_id)
        )

        result = await db.execute(stmt)
        info = result.mappings().all()
        # Group the results by round_name
        grouped = {}
        for row in info:
            round_name = row["round_name"]
            user_data = {
                "qualifier_id" : row["qualifier_id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "email" : row["email"]
            }
            if round_name not in grouped:
                grouped[round_name] = {"round_name": round_name, "qualifier": []}
            
            grouped[round_name]["qualifier"].append(user_data)

        return list(grouped.values())
        
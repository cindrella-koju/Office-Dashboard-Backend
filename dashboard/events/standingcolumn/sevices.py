from sqlalchemy.ext.asyncio import AsyncSession
from events.standingcolumn.schema import CreateColumn, EditColumn
from models import StandingColumn, Qualifier, ColumnValues
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from exception import HTTPInternalServer
from events.standingcolumn.crud import extract_column_by_id
from uuid import UUID

class StandingColumnServices:
    @staticmethod
    async def create_column(
        db: AsyncSession,
        columnDetail: CreateColumn
    ):
        try:
            new_column = StandingColumn(
                stage_id=columnDetail.stage_id,
                column_field=columnDetail.column_field,
                default_value=columnDetail.default_value,
            )

            db.add(new_column)
            await db.flush()

            # Get all users for this stage
            stmt = select(Qualifier.user_id).where(Qualifier.stage_id == columnDetail.stage_id)
            result = await db.execute(stmt)
            users = result.scalars().all()

            # Create default column values for each user
            if users:
                user_standing_col = [
                    ColumnValues(
                        user_id=user_id,
                        column_id=new_column.id,
                        value=columnDetail.default_value
                    )
                    for user_id in users
                ]
                db.add_all(user_standing_col)

            await db.commit()

            return {
                "message": "Column Added successfully",
                "id": new_column.id
            }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to create Column")
        
    @staticmethod
    async def edit_column(db : AsyncSession, columnDetail : EditColumn, column_id : UUID):
        column = await extract_column_by_id(db=db, column_id=column_id)

        if columnDetail.stage_id:
            column.stage_id = columnDetail.stage_id

        if columnDetail.column_field:
            column.column_field = columnDetail.column_field

        await db.commit()

        return {
            "message" : "Stage Update Successfully",
        }
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from models import User, StandingColumn, ColumnValues

class OverallTiesheetServices:

    @staticmethod
    async def retrieve_overall_points_by_round_and_event(
        db: AsyncSession,
        event_id: UUID,
        stage_id: UUID | None = None
    ):
        stmt = select(StandingColumn.column_field).where(
            StandingColumn.stage_id == stage_id
        )
        result = await db.execute(stmt)
        column_fields = result.scalars().all()

        pivot_columns = [ColumnValues.user_id,User.username]
        points_column = None

        for column in column_fields:
            expr = func.max(
                case(
                    (StandingColumn.column_field == column, ColumnValues.value),
                    else_=None
                )
            ).label(column)

            pivot_columns.append(expr)

            if column.lower() == "points":
                points_column = expr

        stmt2 = (
            select(*pivot_columns)
            .join(StandingColumn, ColumnValues.column_id == StandingColumn.id)
            .join(User,User.id == ColumnValues.user_id)
            .group_by(ColumnValues.user_id, User.username)
        )

        if points_column is not None:
            stmt2 = stmt2.order_by(points_column.desc())

        result = await db.execute(stmt2)
        users_col_value = result.mappings().all()

        return users_col_value

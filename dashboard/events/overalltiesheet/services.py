from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from models import User, StandingColumn, ColumnValues


class OverallTiesheetServices:

    @staticmethod
    async def retrieve_overall_points_by_round_and_event(
        db: AsyncSession,
        event_id: UUID,
        page: int,
        limit: int,
        stage_id: UUID | None = None,
    ):
        skip = (page - 1) * limit

        # Get column field for stage
        column_stmt = select(StandingColumn.column_field)

        if stage_id is not None:
            column_stmt = column_stmt.where(
                StandingColumn.stage_id == stage_id
            )

        result = await db.execute(column_stmt)
        column_fields = result.scalars().all()

        pivot_columns = [ColumnValues.user_id, User.username]
        points_label = None

        # Pivot expression
        for column in column_fields:
            label_name = column.lower()

            expr = func.max(
                case(
                    (StandingColumn.column_field == column, ColumnValues.value),
                    else_=None
                )
            ).label(label_name)

            pivot_columns.append(expr)

            if label_name == "points":
                points_label = label_name

        base_query = (
            select(*pivot_columns)
            .join(StandingColumn, ColumnValues.column_id == StandingColumn.id)
            .join(User, User.id == ColumnValues.user_id)
            .group_by(ColumnValues.user_id, User.username)
        )

        if stage_id is not None:
            base_query = base_query.where(
                StandingColumn.stage_id == stage_id
            )

        count_query = (
            select(func.count(func.distinct(ColumnValues.user_id)))
            .join(StandingColumn, ColumnValues.column_id == StandingColumn.id)
        )

        if stage_id is not None:
            count_query = count_query.where(
                StandingColumn.stage_id == stage_id
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Ordering
        if points_label:
            base_query = base_query.order_by(
                func.max(
                    case(
                        (StandingColumn.column_field == "points", ColumnValues.value),
                        else_=None
                    )
                ).desc()
            )
        final_query = base_query.offset(skip).limit(limit)

        result = await db.execute(final_query)
        users_col_value = result.mappings().all()

        return {
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit else 1,
            "total_items": total,
            "items": users_col_value,
        }
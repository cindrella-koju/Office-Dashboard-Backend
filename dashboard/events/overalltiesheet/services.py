from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, cast, Integer
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

        # Get column fields for stage
        column_stmt = select(StandingColumn.column_field)

        if stage_id is not None:
            column_stmt = column_stmt.where(
                StandingColumn.stage_id == stage_id
            )

        result = await db.execute(column_stmt)
        column_fields = result.scalars().all()

        pivot_columns = [ColumnValues.user_id, User.username]
        points_expr = None  # store real SQL expression

        # Build pivot columns
        for column in column_fields:
            label_name = column.lower()

            expr = func.max(
                case(
                    (
                        StandingColumn.column_field == column,
                        cast(ColumnValues.value, Integer)
                    ),
                    else_=None
                )
            ).label(label_name)

            pivot_columns.append(expr)

            if label_name == "points":
                points_expr = expr  

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

        # Count query
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

        # ✅ Correct ordering by points DESC
        if points_expr is not None:
            base_query = base_query.order_by(None)  # clear old order
            base_query = base_query.order_by(points_expr.desc())

        final_query = base_query.offset(skip).limit(limit)

        print("Final Query:", final_query)

        result = await db.execute(final_query)
        users_col_value = result.mappings().all()

        print("User column value:", users_col_value)

        return {
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit, 
            "total_items": total,
            "items": users_col_value,
        }
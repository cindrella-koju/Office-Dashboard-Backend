from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from models import User, Stage, StandingColumn, Qualifier, ColumnValues
from events.overalltiesheet.schema import Round
import json

class OverallTiesheetServices:

    @staticmethod
    async def retrieve_overall_points_by_round_and_event(
        db: AsyncSession,
        event_id: UUID,
        stage_id: UUID | None = None
    ):
        stmt = (
            select(
                User.id.label("id"),
                User.username.label("username"),
                Stage.name.label("round_name"),
                StandingColumn.column_field.label("column_field"),
                ColumnValues.value.label("value"),
            )
            .join(Qualifier, Qualifier.user_id == User.id)
            .join(Stage, Stage.id == Qualifier.stage_id)
            .join(StandingColumn, StandingColumn.stage_id == Stage.id)
            .join(
                ColumnValues,
                and_(
                    ColumnValues.column_id == StandingColumn.id,
                    ColumnValues.user_id == User.id,
                ),
            )
            .where(Qualifier.event_id == event_id)
        )

        if stage_id:
            stmt = stmt.where(Qualifier.stage_id == stage_id)

        result = await db.execute(stmt)
        users = result.mappings().all()

        return OverallTiesheetServices.response_format(users)

    @staticmethod
    def response_format(users: list):
        rounds_dict: dict = {}

        for row in users:
            round_name = row["round_name"]
            user_id = row["id"]

            col_value = {
                "column_name": row["column_field"],
                "column_value": row["value"],
            }

            # Create round if not exists
            if round_name not in rounds_dict:
                rounds_dict[round_name] = {
                    "round_name": round_name,
                    "users": {},
                }

            round_users = rounds_dict[round_name]["users"]

            # Create user if not exists in this round
            if user_id not in round_users:
                round_users[user_id] = {
                    "user_id": user_id,
                    "username": row["username"],
                    "column_detail": [],
                }

            # Append column detail
            round_users[user_id]["column_detail"].append(col_value)

        # Convert user dicts → lists and validate with Pydantic
        formatted_rounds = []
        for round_data in rounds_dict.values():
            round_data["users"] = list(round_data["users"].values())
            formatted_rounds.append(Round.model_validate(round_data))
        
        for user in formatted_rounds:
            print("\n\n\n\nUsers",user.users)
        # for round_ in formatted_rounds:
        #     round_["users"].sort(
        #         key=lambda u: int(next(c["column_value"] for c in u["column_detail"] if c["column_name"] == "Points")),
        #         reverse=True
        #     )
        return formatted_rounds

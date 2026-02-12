from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select
from models import Stage
from fastapi import HTTPException, status

class StageServices:
    @staticmethod
    async def validate_stage(
        db : AsyncSession,
        stage_id : UUID
    ):
        result = await db.execute(select(Stage).where(Stage.id == stage_id))
        stage = result.scalar_one_or_none()

        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Round not found"
            )
        
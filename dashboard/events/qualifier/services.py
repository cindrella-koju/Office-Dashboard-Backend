from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import Qualifier, User
from sqlalchemy import select
from fastapi import HTTPException, status

class QualifierService:
    @staticmethod
    async def validate_qualifier(
        db: AsyncSession,
        qualifier_id : UUID
    ):
        result = await db.execute(select(Qualifier).where(Qualifier.id == qualifier_id))
        qualifier = result.scalar_one_or_none()

        if not qualifier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Qualifier not found"
            )
    
    @staticmethod
    async def extract_username_from_qualifier_id(
        db : AsyncSession,
        qualifier_id : UUID
    ):
        await QualifierService.validate_qualifier(db = db,qualifier_id=qualifier_id)
        result = await db.execute(
            select(User.username).join(Qualifier,Qualifier.user_id == User.id).where(Qualifier.id == qualifier_id)
        )
        return result.scalar_one_or_none()
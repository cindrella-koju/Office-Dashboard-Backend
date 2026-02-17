from models import User,Stage, Qualifier
from fastapi import APIRouter, Depends
from db_connect import get_db_session
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from events.qualifier.services import QualifierService
from events.qualifier.schema import QualifierByRound, QualifierModel



router = APIRouter()

@router.get("")
async def retrieve_qualifier_by_round(stage_id : UUID,  db: Annotated[AsyncSession, Depends(get_db_session)]):
    stmt = select(Qualifier.user_id.label("id"), User.username).join(User,User.id == Qualifier.user_id).where(Qualifier.stage_id == stage_id )
    result = await db.execute(stmt)
    users = result.all()

    return [QualifierByRound.model_validate(user) for user in users]

@router.post("")
async def create_qualifier(
    event_id: UUID,
    stage_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    qualifier: QualifierModel
):
    return await QualifierService.create_qualifier(db=db, qualifier=qualifier, event_id=event_id, stage_id=stage_id)

@router.get("/event")
async def retrieve_qualifiers_by_event(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    return await QualifierService.retrieve_qualifier_by_event(db=db, event_id=event_id)

@router.delete("/{qualifier_id}")
async def delete_qualifier(
    qualifier_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    qualifier =  await QualifierService.extract_username_from_qualifier_id(db = db, qualifier_id=qualifier_id)
    stmt = delete(Qualifier).where(Qualifier.id == qualifier_id)
    await db.execute(stmt)
    await db.commit()

    return{
        "message" : f"Qualifier {qualifier} deleted successfully"
    }

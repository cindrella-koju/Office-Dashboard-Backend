from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from models import Stage
from events.stage.schema import StageDetail, EditStageDetail, StageResponse
from events.stage.crud import extract_stage_by_id, extract_stage_by_event

class StageServices:
    @staticmethod
    async def create_stage( db : AsyncSession, stage:StageDetail, event_id : UUID):
        new_state = Stage(
            event_id = event_id,
            name = stage.name,
        )
        db.add(new_state)
        await db.commit()
        return{
            "message" : "Stage added successfully",
        }
    
    @staticmethod
    async def edit_stage(db:AsyncSession, stage_detail:EditStageDetail, stage_id : UUID):
        stage = await extract_stage_by_id(db = db, stage_id=stage_id)

        if stage_detail.name:
            stage.name = stage_detail.name

        await db.commit()

        return {
            "message" : f"Stage {stage.name} updated to {stage_detail.name} Successfully",
        }
    
    @staticmethod
    async def retrieve_stage(db:AsyncSession, event_id : UUID, stage_id : UUID | None = None):
        if stage_id:
            stage = await extract_stage_by_id(db=db, stage_id=stage_id)
            return StageResponse.model_validate(stage)
        else: 
            stages = await extract_stage_by_event(db=db, event_id=event_id)
            return [StageResponse.model_validate(stage) for stage in stages]


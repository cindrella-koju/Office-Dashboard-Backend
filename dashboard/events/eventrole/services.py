from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from events.eventrole.schema import createEventRole, EventRoleResponse, EditEventRole
from models import UserRole, User, Role
from sqlalchemy.exc import SQLAlchemyError
from exception import HTTPInternalServer
from sqlalchemy import select, delete, func
from events.eventrole.crud import extract_event_role_by_id

class EventRoleServices:
    @staticmethod
    async def create_event_role( db :AsyncSession, event_id : UUID, eventrole: createEventRole):
        try:
            new_event_role = UserRole(
                user_id = eventrole.user_id,
                event_id = event_id,
                role_id = eventrole.role_id
            )
            db.add(new_event_role)
            await db.commit()
            return{
                "message" : "EventRole added successfully"
            }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to create Event Role")
        
    @staticmethod
    async def get_event_role(
        db: AsyncSession,
        event_id: UUID,
        page: int,
        limit: int,
        role_id: UUID | None = None
    ):
        try:
            skip = (page - 1) * limit

            base_stmt = (
                select(
                    UserRole.id,
                    User.username,
                    UserRole.user_id,
                    Role.rolename,
                    UserRole.role_id
                )
                .join(User, User.id == UserRole.user_id)
                .join(Role, Role.id == UserRole.role_id)
                .where(UserRole.event_id == event_id)
            )

            if role_id:
                base_stmt = base_stmt.where(UserRole.role_id == role_id)

            count_stmt = select(func.count()).select_from(
                base_stmt.subquery()
            )

            total_result = await db.execute(count_stmt)
            total = total_result.scalar_one()

            stmt = base_stmt.offset(skip).limit(limit)

            result = await db.execute(stmt)
            event_roles = result.mappings().all()

            return {
                "page": page,
                "limit": limit,
                "total_pages" : (total + limit -1) // limit,
                "data": [
                    EventRoleResponse.model_validate(er)
                    for er in event_roles
                ]
            }

        except SQLAlchemyError:
            await db.rollback()
            raise HTTPInternalServer("Failed to fetch Event Role")
    
    @staticmethod
    async def edit_event_role( db: AsyncSession, event_role_id : UUID, editeventrole : EditEventRole):
        try:
            event_role = await extract_event_role_by_id(db=db,event_role_id=event_role_id)
            
            if editeventrole.user_id != "":
                event_role.user_id = editeventrole.user_id

            if editeventrole.role_id != "":
                event_role.role_id = editeventrole.role_id

            await db.commit()
            return{
                "message" : "Event Role updated successfully"
            }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to edit Event Role")
        
    @staticmethod
    async def delete_event_role(db : AsyncSession, event_role_id : UUID):
        try:
            await extract_event_role_by_id(db=db, event_role_id=event_role_id)

            stmt = delete(UserRole).where(UserRole.id == event_role_id)
            await db.execute(stmt)
            await db.commit()

            return {
                "message" : "Event Role deleted successfully"
            }
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPInternalServer("Failed to delete Event Role")

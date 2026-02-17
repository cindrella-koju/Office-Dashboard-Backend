import asyncio
from sqlalchemy.exc import SQLAlchemyError
from db_connect import AsyncSessionLocal
from models import Role, User, RoleAccessPage, UserRole
from users.services import get_password_hash

async def seed():
    async with AsyncSessionLocal() as db:
        try:
            super_admin_role = Role(
                rolename="superadmin",
                can_edit=True,
                can_create=True,
                can_delete=True,
                can_edit_users=True,
                can_create_users=True,
                can_delete_users=True,
                can_edit_roles=True,
                can_create_roles=True,
                can_delete_roles=True,
                can_edit_events=True,
                can_create_events=True,
                can_delete_events=True,
            )
            db.add(super_admin_role)
            await db.flush()

            superadmin_roleaccesspage = RoleAccessPage(
                role_id=super_admin_role.id,
                home_page=True,
                event_page=True,
                user_page=True,
                profile_page=True,
                tiesheet_page=True,
                group_page=True,
                round_config_page=True,
                qualifier_page=True,
                participants_page=True,
                column_config_page=True,
                group_stage_standing_page=True,
                todays_game_page=True,
                role_page=True
            )
            db.add(superadmin_roleaccesspage)
            await db.flush()

            super_admin_user = User(
                username="teslatech admin",
                fullname="Teslatech",
                email="superadmin.teslatech@gmail.com",
                password= await get_password_hash("Teslatech@superadmin")
            )
            db.add(super_admin_user)
            await db.flush()

            user_role = UserRole(
                user_id=super_admin_user.id,
                role_id=super_admin_role.id
            )
            db.add(user_role)
            
            member_role = Role(
                rolename="member",
                can_edit=False,
                can_create=False,
                can_delete=False,
                can_edit_users=False,
                can_create_users=False,
                can_delete_users=False,
                can_edit_roles=False,
                can_create_roles=False,
                can_delete_roles=False,
                can_edit_events=False,
                can_create_events=False,
                can_delete_events=False,
            )
            db.add(member_role)
            await db.flush()

            member_roleaccesspage = RoleAccessPage(
                role_id=member_role.id,
                home_page=True,
                event_page=True,
                user_page=False,
                profile_page=True,
                tiesheet_page=True,
                group_page=True,
                round_config_page=False,
                qualifier_page=True,
                participants_page=True,
                column_config_page=False,
                group_stage_standing_page=True,
                todays_game_page=True,
                role_page=False
            )
            db.add(member_roleaccesspage)
            await db.flush()
            await db.commit()
            print("Database Seeded Successfully")

        except SQLAlchemyError as e:
            await db.rollback()
            print("Failed to seed data:", str(e))


if __name__ == "__main__":
    asyncio.run(seed())

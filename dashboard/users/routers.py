from fastapi import APIRouter,Depends, HTTPException, status, Header
from users.schema import UserDetail,UserDetailResponse, LoginUser, EditUserDetail
from models import User
from db_connect import get_db_session
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
from uuid import UUID
from users.services import login_user_service, signup_user_services, get_user_by_role, edit_user_services
from dependencies import get_current_user
router = APIRouter()

@router.post("/signup")
async def signup_user(user_data : UserDetail, db : Annotated[AsyncSession,Depends(get_db_session)] ):
    """
        Create new user and assign role member to that user
    """
    await signup_user_services(db, user_data)
    return {"message": "User created successfully"}
        
    
@router.post("/login")
async def login_user(user : LoginUser, db: Annotated[AsyncSession, Depends(get_db_session)]):
    access_token, refresh_token= await login_user_service(db = db, login_data=user)

    return {
        "message": "Login successfully",
        "authorization": "Bearer",
        "access_token": access_token,
        "refresh_token" : refresh_token
    }

@router.get("")
async def retrieve_user(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    role_id : str | None = None,
    current_user: dict = Depends(get_current_user),
):  
    users = await get_user_by_role(db=db, role_id=role_id)
    if not users:
        return{
            "message" : "User not found"
        }

    return [UserDetailResponse.model_validate(user) for user in users]

@router.patch("/{user_id}")
async def edit_user(    
    edit_detail : EditUserDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    return await edit_user_services(db=db, user_data=edit_detail, user_id=user_id)

@router.delete("/user/{user_id}")
async def delete_user(    
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
    
    stmt = delete(User).where(User.id == user_id)
    await db.execute(stmt)
    await db.commit()

    return {"message": f"User {user.username} deleted successfully"}

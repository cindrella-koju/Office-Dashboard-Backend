from fastapi import APIRouter,Depends
from users.schema import UserDetail,UserDetailResponse, LoginUser, EditUserDetail, RefreshTokenRequest, TokenResponse
from models import User
from db_connect import get_db_session
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
from uuid import UUID
from users.services import login_user_service, signup_user_services, edit_user_services, refresh_access_token_service
from users.crud import get_user_by_role, get_user_by_id
from dependencies import get_current_user
from exception import HTTPNotFound

router = APIRouter()

@router.post("/signup")
async def signup_user(
    user_data : UserDetail,
    db : Annotated[AsyncSession,Depends(get_db_session)] 
):
    """
        Create new user and assign role member to that user
    """
    await signup_user_services(db, user_data)
    return {"message": "User created successfully"}
        
    
@router.post("/login")
async def login_user(
    user : LoginUser, 
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    access_token, refresh_token= await login_user_service(db = db, login_data=user)

    return {
        "message": "Login successfully",
        "authorization": "Bearer",
        "access_token": access_token,
        "refresh_token" : refresh_token
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Refresh access token using refresh token
    """
    access_token, refresh_token = await refresh_access_token_service(
        db=db, 
        refresh_token=token_request.refresh_token
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.get("", dependencies=[Depends(get_current_user)])
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

@router.patch("/{user_id}", dependencies=[Depends(get_current_user)])
async def edit_user(    
    edit_detail : EditUserDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    return await edit_user_services(db=db, user_data=edit_detail, user_id=user_id)

@router.delete("/user/{user_id}", dependencies=[Depends(get_current_user)])
async def delete_user(    
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID,
    # current_user: dict = Depends(get_current_user)
):
    user = get_user_by_id(db=db, user_id=user_id)

    if not user:
        raise HTTPNotFound("User not found")
    
    stmt = delete(User).where(User.id == user_id)
    await db.execute(stmt)
    await db.commit()

    return {"message": f"User {user.username} deleted successfully"}

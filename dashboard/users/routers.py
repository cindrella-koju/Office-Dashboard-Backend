from fastapi import APIRouter,Depends, HTTPException, status, Header
from users.schema import UserDetail, RoleEnum, UserDetailResponse, LoginUser, EditUserDetail
from models import User
from db_connect import get_db_session
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
from uuid import UUID
from users.services import get_all_users,get_password_hash, verify_password, generate_jwt_token, verify_jwt_token
from dependencies import get_current_user

router = APIRouter()

@router.post("/signup")
async def signup_user(user : UserDetail, db : Annotated[AsyncSession,Depends(get_db_session)] ):
    users = await get_all_users(db=db)
    for db_user in users:
        if db_user.email == user.email:
            raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail = "Email already exists"
            )
        if db_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exist"
            )
        
    user = User(
        username = user.username,
        fullname = user.fullname,
        email = user.email,
        role = RoleEnum(user.role.value),
        password = await get_password_hash(user.password)
    )

    db.add(user)
    await db.commit()
    return {
        "message" : "User created Successfully",
        "id" : user.id
    }

@router.post("/login")
async def login_user(user : LoginUser, db: Annotated[AsyncSession, Depends(get_db_session)]):
    result = await db.execute(select(User).where(User.username == user.username))
    obtained_user = result.scalars().first()
    verifypassword = await verify_password(user.password, obtained_user.password)

    if verifypassword:
        jwt_token = await generate_jwt_token(user_id=obtained_user.id, role=obtained_user.role)
        return {
            "message" : "Login Successfully",
            "authorization" : "Bearer",
            "token" : jwt_token
        }

@router.get("")
async def retrieve_user(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID | None = None,
    # current_user: dict = Depends(get_current_user),
):  
    # if current_user["role"] == RoleEnum.superadmin or current_user["role"] == RoleEnum.admin:
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserDetailResponse(**user.__dict__)
    else:
        users = await get_all_users(db=db)
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No users found"
            )
        return [UserDetailResponse(**user.__dict__) for user in users]
    # raise HTTPException(
    #     detail="No Access",
    #     status_code=status.HTTP_403_FORBIDDEN
    # )

@router.patch("")
async def edit_user(    
    edit_detail : EditUserDetail,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID | None = None,
    # current_user: dict = Depends(get_current_user),
):
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id required")
    # if current_user["role"] == RoleEnum.superadmin:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if edit_detail.username:
        users = await get_all_users(db=db)
        for db_user in users:
            if db_user.username == user.username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exist"
                )
        user.username = edit_detail.username

    if edit_detail.fullname:
        user.fullname = edit_detail.fullname

    if edit_detail.email:
        users = await get_all_users(db=db)
        for db_user in users:
            if db_user.email == user.email:
                raise HTTPException(
                    status_code = status.HTTP_409_CONFLICT,
                    detail = "Email already exists"
                )
        user.email = edit_detail.email


    if edit_detail.role:
        user.role = edit_detail.role

    await db.commit()

    return {
        "message" : "User updated successfully",
        "user_id" : user.id
    }
    # raise HTTPException(
    #     detail="Not Authorized",
    #     status_code=status.HTTP_403_FORBIDDEN
    # )

@router.delete("/user")
async def delete_user(    
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID | None = None,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != RoleEnum.superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id required")

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

    return {"message": f"User {user_id} deleted successfully"}

# @router.get("/")
# async def generate_field(page:str):
#     if page == "event":
#         return(
#             "title" : "string"
#             "description" : "string or none",
#             "start date": "date",
#             "end date" : "date",
#             "status" : ["draft","active","completed"],
#             "progress_note" : "string or none"
#         )
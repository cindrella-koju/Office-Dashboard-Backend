from models import User, UserRole
from fastapi import HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pwdlib import PasswordHash
import jwt
from uuid import UUID
from dotenv import load_dotenv
import os
from datetime import datetime,timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from roles.services import get_member_role_id
from roles.crud import get_user_role
from users.crud import get_user_by_email_or_username, get_user_with_roles_by_username, get_user_by_id
from sqlalchemy.exc import SQLAlchemyError
from exception import HTTPConflict, HTTPNotFound, HTTPInternalServer, HTTPUnauthorized

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_MINUTES = os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")

password_hash = PasswordHash.recommended()
security = HTTPBearer()

async def get_password_hash(password):
    return password_hash.hash(password)

async def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

async def generate_access_token(user_id : UUID, role_id : UUID,role : str):
    expire = datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(user_id),
        "role_id": str(role_id),
        "role": role,
        "type": "access",
        "exp": expire
    }

    token = jwt.encode(payload=payload,key=SECRET_KEY, algorithm=ALGORITHM)

    return token

async def generate_refresh_token(user_id : UUID):
    expire = datetime.utcnow() + timedelta(days=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire
    }
    token = jwt.encode(payload=payload,key=SECRET_KEY, algorithm=ALGORITHM)
    return token

async def verify_jwt_token(credential: HTTPAuthorizationCredentials = Depends(security)):
    # Actual JWT token  
    token = credential.credentials
    try:
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Decoded JWT:", payload)
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")



async def login_user_service(db : AsyncSession, login_data):
    """
        Service for login User
    """

    user = await get_user_with_roles_by_username(
        db,
        username=login_data.username
    )
    if not user:
        raise HTTPUnauthorized("Invalid username or password")

    # verify password
    is_valid = await verify_password(
        login_data.password,
        user.password
    )

    if not is_valid:
        raise HTTPUnauthorized("Invalid username or password")
    
    if not user.userrole:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no assigned role"
        )
    
    role = user.userrole[0].role  # assuming single role per user

    # retrieve access token
    access_token = await generate_access_token(
        user_id=user.id,
        role=role.rolename,
        role_id=role.id
    )
    # retrieve refresh token
    refresh_token = await generate_refresh_token(
        user_id=user.id
    )

    return access_token, refresh_token


async def signup_user_services(db : AsyncSession, user_data):
    """Services for signup"""
    existing_user = await get_user_by_email_or_username(
        db,
        email=user_data.email,
        username=user_data.username
    )

    # Validate wheather user exist or not
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPConflict("Email alredy exist")
        raise HTTPConflict("Username already exist")

    if user_data.role_id:
        role_id = user_data.role_id
    else:
        role_id = await get_member_role_id(db)
    # Check wheather member role exist or not
    if not role_id:
        raise HTTPNotFound("Role not found")
    
    try:
         # create new User
        new_user = User(
            username = user_data.username,
            fullname = user_data.fullname,
            email = user_data.email,
            password = await get_password_hash(user_data.password)
        )

        db.add(new_user)
        await db.flush()

        # Assign role to user
        user_role = UserRole(
            user_id = new_user.id,
            role_id = role_id
        ) 
        db.add(user_role)
        await db.commit()

        return new_user
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPInternalServer("Failed to create user")
    

async def edit_user_services(db: AsyncSession, user_data, user_id: UUID):
    user = await get_user_by_id( db=db , user_id=user_id)
    if not user:
        raise HTTPNotFound("User not found")

    if user_data.role_id:
        role = await get_user_role(db = db, user_id=user_id)
        if not role:
            raise HTTPNotFound("Role not found")

    # Check for username/email conflicts
    if user_data.username:
        existing_user = await get_user_by_email_or_username(db, username=user_data.username)
        if existing_user and existing_user.id != user.id:
            raise HTTPConflict("Username already exist")

    if user_data.email:
        existing_user = await get_user_by_email_or_username(db, email=user_data.email)
        if existing_user and existing_user.id != user.id:
            raise HTTPConflict("Email already exist")

    # Update fields
    if user_data.fullname:
        user.fullname = user_data.fullname
    if user_data.username:
        user.username = user_data.username
    if user_data.email:
        user.email = user_data.email
    if user_data.role_id:
        role.role_id = user_data.role_id

    await db.commit()
    return {"message": "User updated successfully"}
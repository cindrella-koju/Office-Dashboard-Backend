from models import User
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pwdlib import PasswordHash
import jwt
from uuid import UUID
from users.schema import UserDetail
from dotenv import load_dotenv
import os
from datetime import datetime,timedelta

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

password_hash = PasswordHash.recommended()

async def get_all_users(db : AsyncSession):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

async def get_password_hash(password):
    return password_hash.hash(password)

async def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

async def generate_jwt_token(user_id : UUID, role : UserDetail):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id" : str(user_id),
        "role" : str(role),
        "exp": expire
    }

    token = jwt.encode(payload=payload,key=SECRET_KEY, algorithm=ALGORITHM)

    return token

async def verify_jwt_token(token: str):
    try:
        parts = token.split()
        if len(parts) != 2:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        auth_type, authtoken = parts
        if auth_type != "Bearer":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        decode_jwt_code = jwt.decode(authtoken, SECRET_KEY, algorithms=[ALGORITHM])
        print("Decoded JWT:", decode_jwt_code)
        return decode_jwt_code

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
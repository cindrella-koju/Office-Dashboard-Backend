from fastapi import Depends, HTTPException, Header, status
from typing import Annotated
from users.services import verify_jwt_token

async def get_current_user(authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
    
    try:
        decoded_token = await verify_jwt_token(authorization)
    except HTTPException as e:
        raise e

    return decoded_token

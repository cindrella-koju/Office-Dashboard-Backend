from fastapi import Depends, HTTPException, Header, status
from typing import Annotated
from users.services import verify_jwt_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credential: HTTPAuthorizationCredentials = Depends(security)):
    if not credential:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
    print("Credentials:", credential)
    try:
        decoded_token = await verify_jwt_token(credential)
    except HTTPException as e:
        raise e

    return decoded_token

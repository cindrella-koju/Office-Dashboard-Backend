from fastapi import Depends, HTTPException, Header, status
from users.services import verify_jwt_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from exception import HTTPUnauthorized

security = HTTPBearer()

async def get_current_user(credential: HTTPAuthorizationCredentials = Depends(security)):
    if not credential:
        raise HTTPUnauthorized("Authorization header missing")
    try:
        decoded_token = await verify_jwt_token(credential)
    except HTTPException as e:
        raise e

    return decoded_token

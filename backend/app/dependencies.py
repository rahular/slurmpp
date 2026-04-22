from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import jwt as jwt_utils
from app.db.database import get_db

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Not authenticated", "code": "UNAUTHORIZED"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt_utils.decode_token(credentials.credentials, expected_type="access")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(e), "code": "INVALID_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(username=payload["sub"], role=payload.get("role", "user"))


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Admin access required", "code": "FORBIDDEN"},
        )
    return user

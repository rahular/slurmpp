from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import jwt as jwt_utils
from app.auth.service import authenticate, hash_password
from app.config import settings
from app.db.crud import count_users, create_user
from app.db.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class SetupRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await authenticate(db, body.username, body.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid credentials", "code": "INVALID_CREDENTIALS"},
        )
    username, role = result
    return TokenResponse(
        access_token=jwt_utils.create_access_token(username, role),
        refresh_token=jwt_utils.create_refresh_token(username),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt_utils.decode_token(body.refresh_token, expected_type="refresh")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(e), "code": "INVALID_TOKEN"},
        )
    username = payload["sub"]

    role = "user"
    if settings.auth_backend == "local":
        from app.db.crud import get_user
        user = await get_user(db, username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        role = user.role
    else:
        role = payload.get("role", "user")

    return TokenResponse(
        access_token=jwt_utils.create_access_token(username, role),
        refresh_token=jwt_utils.create_refresh_token(username),
    )


@router.get("/me")
async def me(db: AsyncSession = Depends(get_db), token: str = Depends(lambda: None)):
    # Actual auth handled by dependency in main app
    pass


@router.post("/setup", status_code=status.HTTP_201_CREATED)
async def setup_admin(body: SetupRequest, db: AsyncSession = Depends(get_db)):
    """First-run admin bootstrap. Only available when no users exist."""
    if settings.auth_backend != "local":
        raise HTTPException(status_code=400, detail="Setup only available for local auth")
    count = await count_users(db)
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Setup already completed", "code": "ALREADY_SETUP"},
        )
    user = await create_user(db, body.username, hash_password(body.password), role="admin")
    return {"username": user.username, "role": user.role}

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy import select

from app.api.deps import CurrentUser, DbDep, TokenDep, require_role
from app.core.config import settings
from app.core.security import ALGORITHM, create_access_token, create_refresh_token, verify_password
from app.models.models import AuditLog, RoleEnum, User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_redis():
    redis_client = Redis.from_url(settings.redis_url)
    try:
        yield redis_client
    finally:
        await redis_client.aclose()

RedisDep = Annotated[Redis, Depends(get_redis)]

async def log_audit(db, user_id: int | None, action: str, request: Request, metadata: dict = None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata_=metadata or {}
    )
    db.add(log)
    await db.commit()

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest, 
    db: DbDep, 
    redis: RedisDep
):
    ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"login_attempts:{ip}"
    
    attempts = await redis.get(rate_limit_key)
    if attempts and int(attempts) >= 5:
        await log_audit(db, None, "LOGIN_RATE_LIMITED", request, {"username": login_data.username})
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in 5 minutes."
        )

    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        await redis.incr(rate_limit_key)
        await redis.expire(rate_limit_key, 300) # 5 minutes
        await log_audit(db, user.id if user else None, "LOGIN_FAILED", request, {"username": login_data.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        await log_audit(db, user.id, "LOGIN_FAILED_INACTIVE", request)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Clear rate limit on success
    await redis.delete(rate_limit_key)

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    await log_audit(db, user.id, "LOGIN_SUCCESS", request)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshRequest, db: DbDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_data.refresh_token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


@router.post("/logout")
async def logout(request: Request, db: DbDep, redis: RedisDep, current_user: CurrentUser, token: TokenDep):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 0)
        if ttl > 0:
            await redis.setex(f"token_blacklist:{token}", ttl, "1")
    except Exception:
        pass
    await log_audit(db, current_user.id, "LOGOUT", request)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: CurrentUser):
    return current_user

@router.get("/admin-only")
async def admin_only_test(
    current_user: User = require_role([RoleEnum.ADMIN]),
):
    return {"message": f"Hello Admin {current_user.username}!"}

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.auth import create_access_token, generate_api_key, get_current_user, hash_password, require_roles, verify_password
from app.config import settings
from app.database import get_db
from app.models import ApiKey, User, UserRole
from app.schemas import ApiKeyCreate, ApiKeyResponse, LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/v1/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expire_minutes * 60)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/api-keys", response_model=ApiKeyResponse)
def create_api_key(
    body: ApiKeyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER)),
):
    raw, prefix, key_hash = generate_api_key()
    key = ApiKey(user_id=user.id, name=body.name, key_hash=key_hash, prefix=prefix, scopes=body.scopes)
    db.add(key)
    db.commit()
    db.refresh(key)
    return ApiKeyResponse(id=key.id, name=key.name, prefix=key.prefix, raw_key=raw)

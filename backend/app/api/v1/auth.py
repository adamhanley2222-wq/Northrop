from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.models.core import AppUser
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(AppUser).filter(AppUser.email == payload.email, AppUser.is_active.is_(True)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserInfo)
def me(user: AppUser = Depends(get_current_user)) -> UserInfo:
    return UserInfo(id=str(user.id), email=user.email, full_name=user.full_name, is_admin=user.is_admin)

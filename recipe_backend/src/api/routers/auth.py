from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from src.api.deps import get_current_active_user
from src.core.config import get_settings
from src.core.security import create_access_token, get_password_hash, verify_password
from src.db import get_db
from src.db.models import User
from src.schemas.auth import LoginRequest, Token
from src.schemas.user import UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, summary="Register a new user")
def register_user(email: EmailStr, password: str, username: str | None = None, db: Session = Depends(get_db)):
    """
    Register a user with email and password.

    Parameters:
    - email: Email string
    - password: Plaintext password
    - username: Optional username

    Returns: UserPublic
    """
    existing = db.query(User).filter(User.email == str(email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(email=str(email), username=username, password_hash=get_password_hash(password), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token, summary="Login and obtain a JWT")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return an access token.

    Body:
    - email
    - password

    Returns: Token
    """
    user = db.query(User).filter(User.email == str(data.email)).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    return Token(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserPublic, summary="Get current authenticated user")
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Requires Bearer token. Returns the current user's public info.
    """
    return current_user

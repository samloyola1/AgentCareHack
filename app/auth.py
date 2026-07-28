"""
Authentication & Authorization
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

# ==========================================================
# Password Hashing
# ==========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

# ==========================================================
# Password Utilities
# ==========================================================

def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )

# ==========================================================
# Authenticate User
# ==========================================================

def authenticate_user(
    db: Session,
    email: str,
    password: str,
):
    """
    Authenticate a user using email/password.
    """

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user

# ==========================================================
# JWT Token Creation
# ==========================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
):
    """
    Create JWT access token.
    """

    payload = data.copy()

    if expires_delta:

        expire = datetime.utcnow() + expires_delta

    else:

        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload.update(
        {
            "exp": expire
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

# ==========================================================
# Current User
# ==========================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Decode JWT token and return current user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if user is None:
        raise credentials_exception

    return user

# ==========================================================
# Active User
# ==========================================================

def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    """
    Ensure the authenticated user is active.
    """

    if hasattr(current_user, "active") and not current_user.active:

        raise HTTPException(
            status_code=400,
            detail="Inactive user."
        )

    return current_user

# ==========================================================
# Role-Based Authorization
# ==========================================================

def require_role(*roles):
    """
    RBAC dependency.

    Example:
        Depends(require_role("admin"))

        Depends(require_role("staff", "admin"))
    """

    def role_checker(
        current_user: User = Depends(
            get_current_active_user
        )
    ):

        if current_user.role not in roles:

            raise HTTPException(
                status_code=403,
                detail="Permission denied."
            )

        return current_user

    return role_checker
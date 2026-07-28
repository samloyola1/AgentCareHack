"""Authentication endpoints used by the Streamlit client."""

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import authenticate_user, create_access_token, get_current_user, hash_password
from app.database import get_db
from app.models import PatientProfile, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "patient"


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == payload.email) | (User.name == payload.username)).first():
        raise HTTPException(status_code=409, detail="An account with that username or email already exists.")

    role = payload.role.lower()
    if role not in {"patient", "staff"}:
        raise HTTPException(status_code=400, detail="Role must be patient or staff.")

    user = User(
        name=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.flush()
    if role == "patient":
        db.add(PatientProfile(user_id=user.id, name=user.name, email=user.email, phone=""))
    db.commit()
    return {"id": user.id, "username": user.name, "email": user.email, "role": user.role}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.email == payload.username) | (User.name == payload.username)).first()
    if user is None or authenticate_user(db, user.email, payload.password) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "patient_id": current_user.patient_profile.id if current_user.patient_profile else None,
    }

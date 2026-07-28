"""Reminder endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Appointment, Reminder, User
from app.schemas import ReminderCreate, ReminderResponse

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.patient_profile is None:
        raise HTTPException(status_code=403, detail="Patient profile is required for this operation.")

    appointment = db.get(Appointment, payload.appointment_id)
    if appointment is None or appointment.patient_id != current_user.patient_profile.id:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    reminder = Reminder(**payload.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/my", response_model=list[ReminderResponse])
def my_reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.patient_profile is None:
        raise HTTPException(status_code=403, detail="Patient profile is required for this operation.")

    return db.query(Reminder).filter(Reminder.patient_id == current_user.patient_profile.id).all()

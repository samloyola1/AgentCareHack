from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    AppointmentRequest,
    RescheduleRequest,
    CancelRequest,
)
from app.services.appointment_service import AppointmentService
from app.auth import get_current_user
from app.models import User

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)


@router.post("/book")
def book_appointment(
    request: AppointmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Book an appointment through the CrewAI workflow.
    """
    service = AppointmentService(db)

    if current_user.patient_profile is None:
        raise HTTPException(
            status_code=403,
            detail="Patient profile is required for this operation.",
        )

    result = service.book(
        patient_id=current_user.patient_profile.id,
        request=request,
    )

    return result


@router.put("/reschedule")
def reschedule_appointment(
    request: RescheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AppointmentService(db)

    if current_user.patient_profile is None:
        raise HTTPException(
            status_code=403,
            detail="Patient profile is required for this operation.",
        )

    return service.reschedule(
        patient_id=current_user.patient_profile.id,
        request=request,
    )


@router.delete("/cancel")
def cancel_appointment(
    request: CancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AppointmentService(db)

    if current_user.patient_profile is None:
        raise HTTPException(
            status_code=403,
            detail="Patient profile is required for this operation.",
        )

    return service.cancel(
        patient_id=current_user.patient_profile.id,
        request=request,
    )


@router.get("/my")
def my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AppointmentService(db)

    if current_user.patient_profile is None:
        raise HTTPException(
            status_code=403,
            detail="Patient profile is required for this operation.",
        )

    return service.get_patient_appointments(
        patient_id=current_user.patient_profile.id
    )


@router.get("/{appointment_id}")
def appointment_details(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AppointmentService(db)

    if current_user.patient_profile is None:
        raise HTTPException(
            status_code=403,
            detail="Patient profile is required for this operation.",
        )

    appointment = service.get_appointment(
        appointment_id=appointment_id,
        patient_id=current_user.patient_profile.id,
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    return appointment
"""Database operations used by the appointments API."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Appointment, AppointmentSlot, Doctor
from app.schemas import AppointmentRequest, CancelRequest, RescheduleRequest


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db

    def book(self, patient_id: int, request: AppointmentRequest) -> dict:
        doctor = (
            self.db.query(Doctor)
            .filter(Doctor.department_id == request.department_id, Doctor.active.is_(True))
            .first()
        )
        if doctor is None:
            return {"success": False, "message": "No active doctor is available."}

        slot = (
            self.db.query(AppointmentSlot)
            .filter(
                AppointmentSlot.doctor_id == doctor.id,
                AppointmentSlot.status == "AVAILABLE",
                AppointmentSlot.start_time >= request.preferred_date,
            )
            .order_by(AppointmentSlot.start_time)
            .first()
        )
        if slot is None:
            return {"success": False, "message": "No appointment slot is available."}

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor.id,
            slot_id=slot.id,
            reason=request.reason,
            status="BOOKED",
        )
        slot.status = "BOOKED"
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return {
            "success": True,
            "appointment_id": appointment.id,
            "doctor_name": doctor.name,
            "appointment_time": slot.start_time,
            "message": "Appointment booked successfully.",
        }

    def reschedule(self, patient_id: int, request: RescheduleRequest) -> dict:
        appointment = self._for_patient(request.appointment_id, patient_id)
        slot = self.db.get(AppointmentSlot, request.new_slot_id)
        if appointment is None or slot is None or slot.status != "AVAILABLE":
            return {"success": False, "message": "Appointment or available slot not found."}
        previous_slot = self.db.get(AppointmentSlot, appointment.slot_id)
        if previous_slot:
            previous_slot.status = "AVAILABLE"
        appointment.slot_id = slot.id
        appointment.doctor_id = slot.doctor_id
        appointment.updated_at = datetime.utcnow()
        slot.status = "BOOKED"
        self.db.commit()
        return {"success": True, "appointment_id": appointment.id, "message": "Appointment rescheduled."}

    def cancel(self, patient_id: int, request: CancelRequest) -> dict:
        appointment = self._for_patient(request.appointment_id, patient_id)
        if appointment is None:
            return {"success": False, "message": "Appointment not found."}
        slot = self.db.get(AppointmentSlot, appointment.slot_id)
        if slot:
            slot.status = "AVAILABLE"
        appointment.status = "CANCELLED"
        appointment.updated_at = datetime.utcnow()
        self.db.commit()
        return {"success": True, "appointment_id": appointment.id, "message": "Appointment cancelled."}

    def get_patient_appointments(self, patient_id: int):
        return self.db.query(Appointment).filter(Appointment.patient_id == patient_id).all()

    def get_appointment(self, appointment_id: int, patient_id: int):
        return self._for_patient(appointment_id, patient_id)

    def _for_patient(self, appointment_id: int, patient_id: int):
        return (
            self.db.query(Appointment)
            .filter(Appointment.id == appointment_id, Appointment.patient_id == patient_id)
            .first()
        )

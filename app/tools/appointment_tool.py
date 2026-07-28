# app/tools/appointment_tool.py

import json
from datetime import datetime

from crewai.tools import tool
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import (
    Doctor,
    Appointment,
    AppointmentSlot,
    PatientProfile,
)


@tool("Appointment Tool")
def AppointmentTool(
    patient_id: int,
    department: str,
    action: str = "book",
    appointment_id: int = None,
):
    """
    Manage patient appointments.

    Actions:
        - book
        - reschedule
        - cancel
    """

    db = SessionLocal()

    try:

        # ------------------------------------------------------
        # Verify patient exists
        # ------------------------------------------------------

        patient = (
            db.query(PatientProfile)
            .filter(PatientProfile.id == patient_id)
            .first()
        )

        if not patient:
            return json.dumps(
                {
                    "status": "error",
                    "message": "Patient not found."
                },
                indent=4
            )

        # ------------------------------------------------------
        # BOOK APPOINTMENT
        # ------------------------------------------------------

        if action == "book":

            doctor = (
                db.query(Doctor)
                .filter(
                    Doctor.department == department,
                    Doctor.active == True
                )
                .first()
            )

            if not doctor:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "No doctor available."
                    },
                    indent=4
                )

            slot = (
                db.query(AppointmentSlot)
                .filter(
                    AppointmentSlot.doctor_id == doctor.id,
                    AppointmentSlot.status == "AVAILABLE"
                )
                .order_by(AppointmentSlot.start_time)
                .first()
            )

            if not slot:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "No available appointment slots."
                    },
                    indent=4
                )

            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                slot_id=slot.id,
                status="BOOKED",
                reason="Administrative Booking",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(appointment)

            slot.status = "BOOKED"

            db.commit()

            db.refresh(appointment)

            return json.dumps(
                {
                    "status": "success",
                    "action": "book",

                    "appointment_id": appointment.id,

                    "doctor": doctor.name,

                    "department": department,

                    "date": str(slot.start_time.date()),

                    "time": str(slot.start_time.time()),

                    "message": "Appointment booked successfully."
                },
                indent=4
            )

        # ------------------------------------------------------
        # RESCHEDULE
        # ------------------------------------------------------

        elif action == "reschedule":

            appointment = (
                db.query(Appointment)
                .filter(Appointment.id == appointment_id)
                .first()
            )

            if not appointment:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "Appointment not found."
                    },
                    indent=4
                )

            old_slot = (
                db.query(AppointmentSlot)
                .filter(AppointmentSlot.id == appointment.slot_id)
                .first()
            )

            if old_slot:
                old_slot.status = "AVAILABLE"

            new_slot = (
                db.query(AppointmentSlot)
                .filter(
                    AppointmentSlot.doctor_id == appointment.doctor_id,
                    AppointmentSlot.status == "AVAILABLE"
                )
                .order_by(AppointmentSlot.start_time)
                .first()
            )

            if not new_slot:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "No slot available for rescheduling."
                    },
                    indent=4
                )

            appointment.slot_id = new_slot.id
            appointment.updated_at = datetime.utcnow()

            new_slot.status = "BOOKED"

            db.commit()

            return json.dumps(
                {
                    "status": "success",
                    "action": "reschedule",

                    "appointment_id": appointment.id,

                    "new_date": str(new_slot.start_time.date()),

                    "new_time": str(new_slot.start_time.time()),

                    "message": "Appointment rescheduled."
                },
                indent=4
            )

        # ------------------------------------------------------
        # CANCEL
        # ------------------------------------------------------

        elif action == "cancel":

            appointment = (
                db.query(Appointment)
                .filter(Appointment.id == appointment_id)
                .first()
            )

            if not appointment:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "Appointment not found."
                    },
                    indent=4
                )

            slot = (
                db.query(AppointmentSlot)
                .filter(AppointmentSlot.id == appointment.slot_id)
                .first()
            )

            if slot:
                slot.status = "AVAILABLE"

            appointment.status = "CANCELLED"
            appointment.updated_at = datetime.utcnow()

            db.commit()

            return json.dumps(
                {
                    "status": "success",
                    "action": "cancel",
                    "appointment_id": appointment.id,
                    "message": "Appointment cancelled successfully."
                },
                indent=4
            )

        # ------------------------------------------------------

        else:

            return json.dumps(
                {
                    "status": "error",
                    "message": "Invalid action."
                },
                indent=4
            )

    except SQLAlchemyError as e:

        db.rollback()

        return json.dumps(
            {
                "status": "error",
                "message": str(e)
            },
            indent=4
        )

    finally:
        db.close()
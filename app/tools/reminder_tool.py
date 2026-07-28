# app/tools/reminder_tool.py

import json
from datetime import datetime, timedelta

from crewai.tools import tool
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import Appointment, Reminder


@tool("Reminder Tool")
def ReminderTool(
    appointment_id: int,
    reminder_type: str = "Appointment Reminder"
):
    """
    Create a reminder for a patient's appointment.

    reminder_type:
        - Appointment Reminder
        - Follow-up
    """

    db = SessionLocal()

    try:

        # ------------------------------------------------------
        # Verify Appointment
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # Prevent Duplicate Reminder
        # ------------------------------------------------------

        existing = (
            db.query(Reminder)
            .filter(
                Reminder.appointment_id == appointment_id,
                Reminder.reminder_type == reminder_type,
                Reminder.status == "Scheduled"
            )
            .first()
        )

        if existing:
            return json.dumps(
                {
                    "status": "exists",
                    "reminder_id": existing.id,
                    "message": "Reminder already exists."
                },
                indent=4
            )

        # ------------------------------------------------------
        # Schedule Reminder
        # ------------------------------------------------------

        slot = appointment.slot

        if reminder_type == "Appointment Reminder":
            scheduled_time = slot.start_time - timedelta(hours=24)

        elif reminder_type == "Follow-up":
            scheduled_time = slot.start_time + timedelta(days=30)

        else:
            scheduled_time = datetime.utcnow()

        # ------------------------------------------------------
        # Save Reminder
        # ------------------------------------------------------

        reminder = Reminder(
            patient_id=appointment.patient_id,
            appointment_id=appointment.id,
            reminder_type=reminder_type,
            scheduled_at=scheduled_time,
            status="Scheduled"
        )

        db.add(reminder)

        db.commit()

        db.refresh(reminder)

        return json.dumps(
            {
                "status": "success",
                "reminder_id": reminder.id,
                "appointment_id": appointment.id,
                "patient_id": appointment.patient_id,
                "reminder_type": reminder.reminder_type,
                "scheduled_at": str(reminder.scheduled_at),
                "message": "Reminder scheduled successfully."
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
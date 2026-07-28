# app/services/notifications.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Reminder, PatientProfile, Appointment

import os


# ==========================================================
# Configuration
# ==========================================================

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

SENDER_EMAIL = os.getenv("SENDER_EMAIL", EMAIL_USERNAME)

ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "False").lower() == "true"


# ==========================================================
# Email Sender
# ==========================================================

def send_email(recipient: str, subject: str, body: str):
    """
    Send an email notification.
    """

    if not ENABLE_EMAIL:
        print("\n==============================")
        print("EMAIL NOTIFICATION")
        print("==============================")
        print(f"To      : {recipient}")
        print(f"Subject : {subject}")
        print(body)
        print("==============================\n")
        return True

    try:

        message = MIMEMultipart()

        message["From"] = SENDER_EMAIL
        message["To"] = recipient
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

        server.starttls()

        server.login(
            EMAIL_USERNAME,
            EMAIL_PASSWORD
        )

        server.sendmail(
            SENDER_EMAIL,
            recipient,
            message.as_string()
        )

        server.quit()

        return True

    except Exception as e:

        print(f"Email Error: {e}")

        return False


# ==========================================================
# Appointment Reminder
# ==========================================================

def send_appointment_reminder(reminder_id: int):
    """
    Send reminder for an appointment.
    """

    db: Session = SessionLocal()

    try:

        reminder = (
            db.query(Reminder)
            .filter(Reminder.id == reminder_id)
            .first()
        )

        if not reminder:
            return False

        appointment = (
            db.query(Appointment)
            .filter(Appointment.id == reminder.appointment_id)
            .first()
        )

        if not appointment:
            return False

        patient = (
            db.query(PatientProfile)
            .filter(PatientProfile.id == reminder.patient_id)
            .first()
        )

        if not patient:
            return False

        body = f"""
Dear {patient.name},

This is a reminder regarding your upcoming hospital appointment.

Appointment ID : {appointment.id}

Status : {appointment.status}

Please arrive at least 15 minutes before your scheduled time.

Thank you.

AgentCare Hospital
"""

        success = send_email(
            patient.email,
            "Appointment Reminder",
            body,
        )

        if success:
            reminder.status = "Sent"
            db.commit()

        return success

    finally:
        db.close()


# ==========================================================
# Follow-up Reminder
# ==========================================================

def send_followup_notification(reminder_id: int):

    db = SessionLocal()

    try:

        reminder = (
            db.query(Reminder)
            .filter(Reminder.id == reminder_id)
            .first()
        )

        if not reminder:
            return False

        patient = (
            db.query(PatientProfile)
            .filter(PatientProfile.id == reminder.patient_id)
            .first()
        )

        if not patient:
            return False

        body = f"""
Hello {patient.name},

This is a friendly reminder to schedule your follow-up visit.

Please contact the hospital if you need assistance.

Thank you,
AgentCare Hospital
"""

        success = send_email(
            patient.email,
            "Follow-up Reminder",
            body,
        )

        if success:
            reminder.status = "Sent"
            db.commit()

        return success

    finally:
        db.close()


# ==========================================================
# Process Pending Reminders
# ==========================================================

def process_pending_reminders():

    db = SessionLocal()

    try:

        reminders = (
            db.query(Reminder)
            .filter(Reminder.status == "Scheduled")
            .all()
        )

        for reminder in reminders:

            if reminder.reminder_type == "Appointment Reminder":

                send_appointment_reminder(reminder.id)

            elif reminder.reminder_type == "Follow-up":

                send_followup_notification(reminder.id)

    finally:

        db.close()
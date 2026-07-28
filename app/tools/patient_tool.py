# app/tools/patient_tool.py

import json
from typing import Optional

from crewai.tools import tool
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import PatientProfile


@tool("Patient Record Tool")
def PatientRecordTool(
    name: str,
    phone: str,
    date_of_birth: Optional[str] = None,
    preferred_language: str = "English",
    emergency_contact: Optional[str] = None,
):
    """
    Create a new patient record if one does not exist.
    Otherwise return the existing patient.
    """

    db = SessionLocal()

    try:

        patient = (
            db.query(PatientProfile)
            .filter(PatientProfile.phone == phone)
            .first()
        )

        if patient:

            return json.dumps(
                {
                    "status": "existing",
                    "patient_id": patient.id,
                    "name": patient.name,
                    "phone": patient.phone,
                    "message": "Existing patient found.",
                },
                indent=4,
            )

        new_patient = PatientProfile(
            name=name,
            phone=phone,
            date_of_birth=date_of_birth,
            preferred_language=preferred_language,
            emergency_contact=emergency_contact,
        )

        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)

        return json.dumps(
            {
                "status": "created",
                "patient_id": new_patient.id,
                "name": new_patient.name,
                "phone": new_patient.phone,
                "message": "Patient successfully registered.",
            },
            indent=4,
        )

    except SQLAlchemyError as e:

        db.rollback()

        return json.dumps(
            {
                "status": "error",
                "message": str(e),
            },
            indent=4,
        )

    finally:
        db.close()
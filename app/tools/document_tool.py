# app/tools/document_tool.py

import os
import json
import hashlib
from datetime import datetime

from crewai.tools import tool
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import PatientProfile, PatientDocument


# Required documents for every patient workflow
REQUIRED_DOCUMENTS = [
    "ECG",
    "Blood Report",
]


def classify_document(filename: str) -> str:
    """
    Classify document type based on filename.
    """

    filename = filename.lower()

    if "ecg" in filename:
        return "ECG"

    elif "blood" in filename:
        return "Blood Report"

    elif "mri" in filename:
        return "MRI"

    elif "ct" in filename:
        return "CT Scan"

    elif "prescription" in filename:
        return "Prescription"

    elif "insurance" in filename:
        return "Insurance"

    elif "discharge" in filename:
        return "Discharge Summary"

    return "Other"


def calculate_checksum(file_path: str) -> str:
    """
    Generate SHA256 checksum.
    """

    sha = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            sha.update(chunk)

    return sha.hexdigest()


@tool("Document Tool")
def DocumentTool(
    patient_id: int,
    file_path: str,
):
    """
    Upload and classify patient documents.

    Detect duplicate uploads using SHA256 checksum.
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Verify Patient
        # ----------------------------------------------------

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
                indent=4,
            )

        # ----------------------------------------------------
        # Verify File Exists
        # ----------------------------------------------------

        if not os.path.exists(file_path):

            return json.dumps(
                {
                    "status": "error",
                    "message": "Uploaded file not found."
                },
                indent=4,
            )

        # ----------------------------------------------------
        # Classify Document
        # ----------------------------------------------------

        filename = os.path.basename(file_path)

        document_type = classify_document(filename)

        checksum = calculate_checksum(file_path)

        # ----------------------------------------------------
        # Duplicate Detection
        # ----------------------------------------------------

        duplicate = (
            db.query(PatientDocument)
            .filter(
                PatientDocument.patient_id == patient_id,
                PatientDocument.checksum == checksum,
            )
            .first()
        )

        if duplicate:

            return json.dumps(
                {
                    "status": "duplicate",
                    "document_id": duplicate.id,
                    "document_type": duplicate.document_type,
                    "message": "Duplicate document detected."
                },
                indent=4,
            )

        # ----------------------------------------------------
        # Save Metadata
        # ----------------------------------------------------

        new_document = PatientDocument(

            patient_id=patient_id,

            document_type=document_type,

            file_path=file_path,

            checksum=checksum,

            document_date=datetime.utcnow(),

            created_at=datetime.utcnow(),
        )

        db.add(new_document)

        db.commit()

        db.refresh(new_document)

        # ----------------------------------------------------
        # Missing Documents
        # ----------------------------------------------------

        uploaded = (
            db.query(PatientDocument.document_type)
            .filter(PatientDocument.patient_id == patient_id)
            .all()
        )

        uploaded_types = [doc[0] for doc in uploaded]

        missing = [
            doc
            for doc in REQUIRED_DOCUMENTS
            if doc not in uploaded_types
        ]

        return json.dumps(
            {
                "status": "success",

                "document_id": new_document.id,

                "document_type": document_type,

                "filename": filename,

                "checksum": checksum,

                "missing_documents": missing,

                "message": "Document uploaded successfully."
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
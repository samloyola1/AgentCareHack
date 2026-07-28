import os
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import (
    User,
    PatientProfile,
    PatientDocument,
    AuditEvent,
)

from app.tools.document_tool import (
    classify_document,
    calculate_checksum,
)

# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_FOLDER = settings.UPLOAD_DIRECTORY

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)


# ==========================================================
# Audit Helper
# ==========================================================

def create_audit_log(
    db: Session,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    metadata: str = "",
):

    audit = AuditEvent(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_metadata=metadata,
        created_at=datetime.utcnow(),
    )

    db.add(audit)
    db.commit()


# ==========================================================
# Upload Document
# ==========================================================

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.id == patient_id)
        .first()
    )

    if patient is None:

        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    filename = (
        f"{patient_id}_{datetime.utcnow().timestamp()}_{file.filename}"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    checksum = calculate_checksum(file_path)

    duplicate = (
        db.query(PatientDocument)
        .filter(
            PatientDocument.patient_id == patient_id,
            PatientDocument.checksum == checksum,
        )
        .first()
    )

    if duplicate:

        os.remove(file_path)

        raise HTTPException(
            status_code=409,
            detail="Duplicate document."
        )

    document_type = classify_document(
        file.filename
    )

    document = PatientDocument(

        patient_id=patient_id,

        document_type=document_type,

        file_path=file_path,

        checksum=checksum,

        document_date=datetime.utcnow(),

        created_at=datetime.utcnow(),
    )

    db.add(document)

    db.commit()

    db.refresh(document)

    create_audit_log(
        db,
        current_user.id,
        "UPLOAD_DOCUMENT",
        "PatientDocument",
        document.id,
    )

    return {

        "success": True,

        "document_id": document.id,

        "document_type": document.document_type,

        "filename": file.filename,

        "message": "Document uploaded successfully."

    }


# ==========================================================
# List Patient Documents
# ==========================================================

@router.get(
    "/patient/{patient_id}"
)
def list_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.id == patient_id)
        .first()
    )

    if patient is None:

        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    documents = (
        db.query(PatientDocument)
        .filter(
            PatientDocument.patient_id == patient_id
        )
        .order_by(
            PatientDocument.created_at.desc()
        )
        .all()
    )

    create_audit_log(
        db,
        current_user.id,
        "VIEW_DOCUMENTS",
        "PatientDocument",
        patient_id,
    )

    return documents


# ==========================================================
# Get Document Details
# ==========================================================

@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    document = (
        db.query(PatientDocument)
        .filter(
            PatientDocument.id == document_id
        )
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    create_audit_log(
        db,
        current_user.id,
        "VIEW_DOCUMENT",
        "PatientDocument",
        document.id,
    )

    return document

# ==========================================================
# Required Documents
# ==========================================================

REQUIRED_DOCUMENTS = [
    "ECG",
    "Blood Report",
]

# ==========================================================
# Delete Document
# ==========================================================

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role.lower() not in {"admin", "staff"}:

        raise HTTPException(
            status_code=403,
            detail="Permission denied."
        )

    document = (
        db.query(PatientDocument)
        .filter(PatientDocument.id == document_id)
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)

    db.commit()

    create_audit_log(
        db,
        current_user.id,
        "DELETE_DOCUMENT",
        "PatientDocument",
        document_id,
    )

    return {

        "success": True,

        "message": "Document deleted successfully."

    }


# ==========================================================
# Download Document
# ==========================================================

@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    document = (
        db.query(PatientDocument)
        .filter(PatientDocument.id == document_id)
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    if not os.path.exists(document.file_path):

        raise HTTPException(
            status_code=404,
            detail="File missing on server."
        )

    create_audit_log(
        db,
        current_user.id,
        "DOWNLOAD_DOCUMENT",
        "PatientDocument",
        document.id,
    )

    return FileResponse(
        document.file_path,
        filename=os.path.basename(document.file_path),
    )


# ==========================================================
# Missing Documents
# ==========================================================

@router.get("/patient/{patient_id}/missing")
def missing_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    uploaded = (
        db.query(PatientDocument.document_type)
        .filter(
            PatientDocument.patient_id == patient_id
        )
        .all()
    )

    uploaded_types = [
        d[0]
        for d in uploaded
    ]

    missing = [

        doc

        for doc in REQUIRED_DOCUMENTS

        if doc not in uploaded_types

    ]

    return {

        "patient_id": patient_id,

        "missing_documents": missing,

        "uploaded_documents": uploaded_types,

    }


# ==========================================================
# Reclassify Document
# ==========================================================

@router.put("/{document_id}/classify")
def reclassify_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role.lower() not in {"admin", "staff"}:

        raise HTTPException(
            status_code=403,
            detail="Permission denied."
        )

    document = (
        db.query(PatientDocument)
        .filter(
            PatientDocument.id == document_id
        )
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    filename = os.path.basename(document.file_path)

    document.document_type = classify_document(
        filename
    )

    db.commit()

    create_audit_log(
        db,
        current_user.id,
        "RECLASSIFY_DOCUMENT",
        "PatientDocument",
        document.id,
    )

    return {

        "success": True,

        "document_id": document.id,

        "new_document_type": document.document_type,

    }


# ==========================================================
# Patient Document Summary
# ==========================================================

@router.get("/patient/{patient_id}/summary")
def patient_document_summary(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    documents = (
        db.query(PatientDocument)
        .filter(
            PatientDocument.patient_id == patient_id
        )
        .all()
    )

    summary = {}

    for doc in documents:

        summary[doc.document_type] = (
            summary.get(doc.document_type, 0) + 1
        )

    return {

        "patient_id": patient_id,

        "total_documents": len(documents),

        "document_summary": summary,

    }


# ==========================================================
# Health Check
# ==========================================================

@router.get("/health")
def health():

    return {

        "status": "healthy",

        "service": "Documents API"

    }

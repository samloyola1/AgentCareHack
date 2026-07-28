"""Staff-only administrative endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Appointment, AuditEvent, Escalation, PatientProfile, User, WorkflowRun

router = APIRouter(prefix="/staff", tags=["Staff"])


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.lower() not in {"staff", "admin"}:
        raise HTTPException(status_code=403, detail="Access denied.")
    return current_user


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return {
        "total_patients": db.query(PatientProfile).count(),
        "total_appointments": db.query(Appointment).count(),
        "pending_escalations": db.query(Escalation).filter(Escalation.status == "Pending").count(),
    }


@router.get("/appointments")
def all_appointments(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return db.query(Appointment).all()


@router.get("/patients")
def all_patients(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return db.query(PatientProfile).all()


@router.get("/escalations")
def escalations(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return db.query(Escalation).all()


@router.post("/escalations/{escalation_id}/approve")
def approve_escalation(
    escalation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    escalation = db.get(Escalation, escalation_id)
    if escalation is None:
        raise HTTPException(status_code=404, detail="Escalation not found.")
    escalation.status = "Approved"
    escalation.reviewed_by = current_user.id
    db.commit()
    return {"success": True, "escalation_id": escalation.id}


@router.get("/workflow/{workflow_id}")
def workflow_history(workflow_id: int, db: Session = Depends(get_db), _: User = Depends(require_staff)):
    workflow = db.get(WorkflowRun, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return workflow


@router.get("/audit")
def audit_logs(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).all()

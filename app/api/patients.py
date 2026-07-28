from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.crews.crew import AgentCareCrew
from app.database import get_db, SessionLocal  # NOTE: adjust "SessionLocal" if your
                                                  # app/database.py names its session
                                                  # factory differently.
from app.models import Appointment, AuditEvent, PatientDocument, PatientProfile, User, WorkflowRun
from app.schemas import PatientCreate, PatientRequest, PatientResponse, PatientUpdate

# -------------------------------------------------------
# Router
# -------------------------------------------------------

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)

# -------------------------------------------------------
# Audit Helper
# -------------------------------------------------------

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


def require_patient_profile(current_user: User) -> PatientProfile:
    """Return the authenticated user's patient profile or raise 404."""
    if current_user.patient_profile is None:
        raise HTTPException(status_code=404, detail="Patient profile not found.")
    return current_user.patient_profile


# =======================================================
# Register Patient
# =======================================================

@router.post(
    "/register",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    existing = (
        db.query(PatientProfile)
        .filter(PatientProfile.phone == patient.phone)
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail="Patient already exists.",
        )

    new_patient = PatientProfile(

        name=patient.name,

        email=patient.email,

        phone=patient.phone,

        date_of_birth=patient.date_of_birth,

        preferred_language=patient.preferred_language,

        emergency_contact=patient.emergency_contact,

        created_at=datetime.utcnow(),

        updated_at=datetime.utcnow(),
    )

    db.add(new_patient)

    db.commit()

    db.refresh(new_patient)

    create_audit_log(
        db=db,
        actor_id=current_user.id,
        action="CREATE_PATIENT",
        entity_type="PatientProfile",
        entity_id=new_patient.id,
    )

    return new_patient


# =======================================================
# Get Patient
# =======================================================

@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.id == patient_id)
        .first()
    )

    if not patient:

        raise HTTPException(
            status_code=404,
            detail="Patient not found.",
        )

    create_audit_log(
        db=db,
        actor_id=current_user.id,
        action="VIEW_PATIENT",
        entity_type="PatientProfile",
        entity_id=patient.id,
    )

    return patient


# =======================================================
# Update Patient
# =======================================================

@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
)
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.id == patient_id)
        .first()
    )

    if not patient:

        raise HTTPException(
            status_code=404,
            detail="Patient not found.",
        )

    update_data = patient_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(patient, key, value)

    patient.updated_at = datetime.utcnow()

    db.commit()

    db.refresh(patient)

    create_audit_log(
        db=db,
        actor_id=current_user.id,
        action="UPDATE_PATIENT",
        entity_type="PatientProfile",
        entity_id=patient.id,
    )

    return patient


# =======================================================
# Get Patient Appointments
# =======================================================

@router.get(
    "/{patient_id}/appointments",
)
def get_patient_appointments(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    appointments = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient_id)
        .all()
    )

    create_audit_log(
        db=db,
        actor_id=current_user.id,
        action="VIEW_APPOINTMENTS",
        entity_type="Appointment",
        entity_id=patient_id,
    )

    return appointments


# =======================================================
# Get Patient Documents
# =======================================================

@router.get(
    "/{patient_id}/documents",
)
def get_patient_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    documents = (
        db.query(PatientDocument)
        .filter(PatientDocument.patient_id == patient_id)
        .all()
    )

    create_audit_log(
        db=db,
        actor_id=current_user.id,
        action="VIEW_DOCUMENTS",
        entity_type="PatientDocument",
        entity_id=patient_id,
    )

    return documents


# =======================================================
# Background worker: runs the crew, using its OWN db session
# (the request-scoped `db` session is closed by the time this
# runs, since the HTTP response has already been sent)
# =======================================================

def run_crew_workflow(workflow_id: int, patient_request: str):
    print(f"🚀 [Workflow {workflow_id}] Background task started.")
    db = SessionLocal()
    try:
        workflow = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()
        if workflow is None:
            print(f"⚠️ [Workflow {workflow_id}] Not found in DB — aborting background task.")
            return

        try:
            print(f"🤖 [Workflow {workflow_id}] Building crew and calling kickoff()...")
            crew = AgentCareCrew()
            result = crew.kickoff(patient_request=patient_request)
            print(f"✅ [Workflow {workflow_id}] Crew finished successfully.")

            workflow.status = "Completed"
            workflow.current_step = "FINISHED"
            workflow.state = str(result)
            workflow.updated_at = datetime.utcnow()
            db.commit()
            print(f"💾 [Workflow {workflow_id}] Status saved as Completed.")

        except Exception as e:
            print(f"❌ [Workflow {workflow_id}] Crew FAILED: {e}")
            workflow.status = "Failed"
            workflow.current_step = "ERROR"
            workflow.state = str(e)
            workflow.updated_at = datetime.utcnow()
            db.commit()
    except Exception as outer_e:
        # Catches failures BEFORE/OUTSIDE the inner try (e.g. DB session
        # itself failing to open, or the query above raising) so nothing
        # fails completely silently.
        print(f"🔥 [Workflow {workflow_id}] Unexpected error in background task: {outer_e}")
    finally:
        db.close()
        print(f"🏁 [Workflow {workflow_id}] Background task finished, DB session closed.")


# =======================================================
# Submit Administrative Request
# =======================================================

@router.post(
    "/request"
)
def submit_patient_request(
    request: PatientRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role.lower() == "patient":
        profile = require_patient_profile(current_user)
        if request.patient_id != profile.id:
            raise HTTPException(status_code=403, detail="Permission denied for this patient request.")

    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.id == request.patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    # --------------------------------------------
    # Create Workflow (status: Running)
    # --------------------------------------------

    workflow = WorkflowRun(

        patient_id=request.patient_id,

        current_step="STARTED",

        state=request.request,

        status="Running",

        created_at=datetime.utcnow(),

        updated_at=datetime.utcnow(),
    )

    db.add(workflow)

    db.commit()

    db.refresh(workflow)

    # --------------------------------------------
    # Schedule CrewAI Workflow to run AFTER this
    # response is sent, instead of blocking here.
    # Poll GET /patients/workflow/{workflow_id} for status.
    # --------------------------------------------

    background_tasks.add_task(run_crew_workflow, workflow.id, request.request)

    # --------------------------------------------
    # Audit Log
    # --------------------------------------------

    create_audit_log(
        db=db,
        actor_id=current_user.id,
        action="START_WORKFLOW",
        entity_type="WorkflowRun",
        entity_id=workflow.id,
    )

    return {

        "workflow_id": workflow.id,

        "status": workflow.status,

        "message": "Workflow started. Poll /patients/workflow/{workflow_id} for status."

    }


# ============================================================
# Search Patients
# ============================================================

@router.get("/search")
def search_patients(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search patients by name, email or phone.
    """

    if current_user.role.lower() not in {"admin", "staff"}:
        raise HTTPException(
            status_code=403,
            detail="Not authorized."
        )

    patients = (
        db.query(PatientProfile)
        .filter(
            or_(
                PatientProfile.name.ilike(f"%{query}%"),
                PatientProfile.email.ilike(f"%{query}%"),
                PatientProfile.phone.ilike(f"%{query}%"),
            )
        )
        .all()
    )

    create_audit_log(
        db,
        current_user.id,
        "SEARCH_PATIENT",
        "PatientProfile",
        0,
        f"Query={query}",
    )

    return patients


# ============================================================
# Workflow History
# ============================================================

@router.get("/{patient_id}/workflows")
def get_patient_workflows(
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

    workflows = (
        db.query(WorkflowRun)
        .filter(WorkflowRun.patient_id == patient_id)
        .order_by(WorkflowRun.created_at.desc())
        .all()
    )

    create_audit_log(
        db,
        current_user.id,
        "VIEW_WORKFLOW_HISTORY",
        "WorkflowRun",
        patient_id,
    )

    return workflows


# ============================================================
# Workflow Status
# ============================================================

@router.get("/workflow/{workflow_id}")
def workflow_status(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    workflow = (
        db.query(WorkflowRun)
        .filter(WorkflowRun.id == workflow_id)
        .first()
    )

    if workflow is None:

        raise HTTPException(
            status_code=404,
            detail="Workflow not found."
        )

    return {

        "workflow_id": workflow.id,

        "patient_id": workflow.patient_id,

        "current_step": workflow.current_step,

        "status": workflow.status,

        "result": workflow.state,

        "created_at": workflow.created_at,

        "updated_at": workflow.updated_at,

    }


# ============================================================
# Soft Delete Patient
# ============================================================

@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete patient.

    Admin only.
    """

    if current_user.role.lower() != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admin access required."
        )

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

    patient.active = False

    patient.updated_at = datetime.utcnow()

    db.commit()

    create_audit_log(
        db,
        current_user.id,
        "DELETE_PATIENT",
        "PatientProfile",
        patient.id,
    )

    return {

        "success": True,

        "message": "Patient deactivated successfully."

    }


# ============================================================
# Current Patient Profile
# ============================================================

@router.get("/me/profile")
def my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    profile = require_patient_profile(current_user)

    patient = db.get(PatientProfile, profile.id)

    if patient is None:

        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    return patient


# ============================================================
# Current Patient Workflow History
# ============================================================

@router.get("/me/workflows")
def my_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    profile = require_patient_profile(current_user)

    workflows = (
        db.query(WorkflowRun)
        .filter(
            WorkflowRun.patient_id == profile.id
        )
        .all()
    )

    return workflows


# ============================================================
# Health Check
# ============================================================

@router.get("/health")
def health():

    return {

        "status": "healthy",

        "service": "Patient API"

    }

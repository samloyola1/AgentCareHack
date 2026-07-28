"""CrewAI tool for creating human-review escalations."""

import json

from crewai.tools import tool
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import Escalation, WorkflowRun


@tool("Escalation Tool")
def EscalationTool(workflow_run_id: int, reason: str):
    """Create a pending human-review escalation for an existing workflow."""
    db = SessionLocal()
    try:
        workflow = db.get(WorkflowRun, workflow_run_id)
        if workflow is None:
            return json.dumps({"status": "error", "message": "Workflow not found."})

        escalation = Escalation(workflow_run_id=workflow_run_id, reason=reason)
        db.add(escalation)
        db.commit()
        db.refresh(escalation)
        return json.dumps(
            {
                "status": "success",
                "escalation_id": escalation.id,
                "message": "Escalated for human review.",
            }
        )
    except SQLAlchemyError as error:
        db.rollback()
        return json.dumps({"status": "error", "message": str(error)})
    finally:
        db.close()

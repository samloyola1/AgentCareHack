# app/tools/audit_tool.py

import json
from datetime import datetime

from crewai.tools import tool
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import AuditEvent


@tool("Audit Log Tool")
def AuditLogTool(
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    metadata: dict = None
):
    """
    Record an audit event in the database.

    Parameters
    ----------
    actor_id : int
        User or agent performing the action.

    action : str
        Action performed.
        Example:
            CREATE_PATIENT
            BOOK_APPOINTMENT
            UPLOAD_DOCUMENT
            CREATE_REMINDER

    entity_type : str
        Type of entity.

    entity_id : int
        Entity primary key.

    metadata : dict
        Additional information.
    """

    db = SessionLocal()

    try:

        if metadata is None:
            metadata = {}

        audit = AuditEvent(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_metadata=json.dumps(metadata),
            created_at=datetime.utcnow()
        )

        db.add(audit)

        db.commit()

        db.refresh(audit)

        return json.dumps(
            {
                "status": "success",
                "audit_event_id": audit.id,
                "message": "Audit event recorded successfully."
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

# app/services/escalations.py

from datetime import datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Escalation


class EscalationService:
    """
    Service for creating and managing workflow escalations.
    """

    @staticmethod
    def create_escalation(
        workflow_run_id: int,
        reason: str,
    ):
        """
        Create a new escalation.
        """

        db: Session = SessionLocal()

        try:

            escalation = Escalation(
                workflow_run_id=workflow_run_id,
                reason=reason,
                status="Pending",
                reviewed_by=None,
                created_at=datetime.utcnow(),
            )

            db.add(escalation)
            db.commit()
            db.refresh(escalation)

            return {
                "success": True,
                "escalation_id": escalation.id,
                "status": escalation.status,
                "reason": escalation.reason,
            }

        except Exception as e:

            db.rollback()

            return {
                "success": False,
                "message": str(e),
            }

        finally:
            db.close()

    # ------------------------------------------------------

    @staticmethod
    def approve_escalation(
        escalation_id: int,
        reviewer_id: int,
    ):
        """
        Approve an escalation.
        """

        db: Session = SessionLocal()

        try:

            escalation = (
                db.query(Escalation)
                .filter(Escalation.id == escalation_id)
                .first()
            )

            if not escalation:
                return {
                    "success": False,
                    "message": "Escalation not found."
                }

            escalation.status = "Approved"
            escalation.reviewed_by = reviewer_id

            db.commit()

            return {
                "success": True,
                "message": "Escalation approved."
            }

        except Exception as e:

            db.rollback()

            return {
                "success": False,
                "message": str(e)
            }

        finally:
            db.close()

    # ------------------------------------------------------

    @staticmethod
    def reject_escalation(
        escalation_id: int,
        reviewer_id: int,
    ):
        """
        Reject an escalation.
        """

        db: Session = SessionLocal()

        try:

            escalation = (
                db.query(Escalation)
                .filter(Escalation.id == escalation_id)
                .first()
            )

            if not escalation:
                return {
                    "success": False,
                    "message": "Escalation not found."
                }

            escalation.status = "Rejected"
            escalation.reviewed_by = reviewer_id

            db.commit()

            return {
                "success": True,
                "message": "Escalation rejected."
            }

        except Exception as e:

            db.rollback()

            return {
                "success": False,
                "message": str(e)
            }

        finally:
            db.close()

    # ------------------------------------------------------

    @staticmethod
    def get_pending_escalations():
        """
        Return all pending escalations.
        """

        db: Session = SessionLocal()

        try:

            escalations = (
                db.query(Escalation)
                .filter(Escalation.status == "Pending")
                .all()
            )

            results = []

            for escalation in escalations:

                results.append(
                    {
                        "id": escalation.id,
                        "workflow_run_id": escalation.workflow_run_id,
                        "reason": escalation.reason,
                        "status": escalation.status,
                        "created_at": str(escalation.created_at),
                    }
                )

            return results

        finally:
            db.close()

    # ------------------------------------------------------

    @staticmethod
    def get_escalation(
        escalation_id: int,
    ):
        """
        Return a single escalation.
        """

        db: Session = SessionLocal()

        try:

            escalation = (
                db.query(Escalation)
                .filter(Escalation.id == escalation_id)
                .first()
            )

            if not escalation:
                return None

            return {
                "id": escalation.id,
                "workflow_run_id": escalation.workflow_run_id,
                "reason": escalation.reason,
                "status": escalation.status,
                "reviewed_by": escalation.reviewed_by,
                "created_at": str(escalation.created_at),
            }

        finally:
            db.close()
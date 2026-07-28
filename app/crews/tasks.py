# app/crews/tasks.py

from crewai import Task


class AgentCareTasks:
    """
    Defines all CrewAI tasks for the AgentCare workflow.
    """

    def __init__(self, agents):
        self.agents = agents

    ####################################################################
    # 1. Registration & Workflow Initialization
    ####################################################################

    def registration_task(self):

        return Task(
            description="""
You are responsible for beginning the patient's administrative workflow.

Your responsibilities are:

1. Identify whether the patient already exists.
2. Create a patient profile if one does not exist.
3. Create a new workflow run.
4. Save the patient's request.
5. Log every action using the audit tool.

Never diagnose or interpret medical information.

Patient Request:
{patient_request}
            """,

            expected_output="""
A structured JSON object containing:

- patient_id
- workflow_id
- patient_status (existing/new)
- request_summary
- workflow_status
            """,

            agent=self.agents.coordinator()
        )

    ####################################################################
    # 2. Department Routing
    ####################################################################

    def routing_task(self):

        return Task(
            description="""
Analyze the patient's administrative request.

Determine the correct hospital department.

Examples include:

- Cardiology
- Neurology
- Pediatrics
- Orthopedics
- General Medicine
- Dermatology
- ENT

If the patient requests:

• diagnosis
• medication advice
• dosage changes
• emergency assistance

DO NOT answer.

Instead create an escalation.

Use the routing tool.

Log every action.
            """,

            expected_output="""
JSON containing:

- detected_intent
- department
- confidence
- escalation_required
- escalation_reason
            """,

            agent=self.agents.routing_agent()
        )

    ####################################################################
    # 3. Appointment Scheduling
    ####################################################################

    def appointment_task(self):

        return Task(
            description="""
Retrieve available doctors.

Retrieve available appointment slots.

Avoid scheduling conflicts.

Book the requested appointment.

If requested:

• reschedule

or

• cancel

perform the requested operation.

Persist the appointment.

Use the appointment tool.

Audit every action.
            """,

            expected_output="""
JSON containing:

- doctor
- department
- appointment_date
- appointment_time
- appointment_status
- appointment_id
            """,

            agent=self.agents.appointment_agent()
        )

    ####################################################################
    # 4. Document Processing
    ####################################################################

    def document_task(self):

        return Task(
            description="""
Process every uploaded patient document.

Responsibilities:

• classify documents

Examples:

- ECG
- Blood Report
- MRI
- CT Scan
- Prescription
- Insurance
- Discharge Summary

Detect:

- duplicate uploads

Determine:

- missing required documents

Store metadata.

Do NOT interpret medical findings.

Use the document tool.
            """,

            expected_output="""
JSON containing:

- uploaded_documents
- classified_documents
- duplicates
- missing_documents
- storage_references
            """,

            agent=self.agents.document_agent()
        )

    ####################################################################
    # 5. Safety Check
    ####################################################################

    def safety_task(self):

        return Task(
            description="""
Review the complete workflow.

Ensure no medical advice has been provided.

Detect:

- diagnosis requests

- prescription requests

- dosage requests

- emergency situations

If unsafe:

Create an escalation.

Otherwise approve the workflow.

Generate reminders and follow-up tasks.

Log everything.
            """,

            expected_output="""
JSON containing:

- safety_status
- reminder_created
- follow_up_created
- escalation_required
- escalation_reason
            """,

            agent=self.agents.safety_agent()
        )

    ####################################################################
    # 6. Final Summary
    ####################################################################

    def summary_task(self):

        return Task(
            description="""
Collect outputs from every previous task.

Prepare the final response for the patient.

The response should include:

• patient registration status

• department assigned

• appointment information

• uploaded documents

• reminder information

• workflow status

Never include diagnosis or treatment recommendations.
            """,

            expected_output="""
A final structured JSON response containing:

{
    "workflow_id": "...",
    "patient_id": "...",
    "department": "...",
    "appointment": {
        "doctor": "...",
        "date": "...",
        "time": "..."
    },
    "documents": [],
    "reminder": "...",
    "status": "Completed"
}
            """,

            agent=self.agents.coordinator()
        )

    ####################################################################
    # Return Workflow
    ####################################################################

    def all_tasks(self):

        return [

            self.registration_task(),

            self.routing_task(),

            self.appointment_task(),

            self.document_task(),

            self.safety_task(),

            self.summary_task()

        ]
# app/crews/agents.py

import os
from pathlib import Path

from crewai import Agent, LLM

# --- Workaround for CrewAI issue #5886 ---
# CrewAI calls mark_cache_breakpoint() on every message for every provider,
# but only its Anthropic adapter knows how to strip that field back out
# before sending the request. Every other provider (Mistral, Groq, etc.)
# receives the raw "cache_breakpoint" key and rejects it, since their APIs
# use strict schema validation that errors on unrecognized fields.
# This patches the function to a no-op so the field is never added at all.
# Remove this block once CrewAI ships an official fix for non-Anthropic providers.
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
    print("🩹 Patched CrewAI: disabled cache_breakpoint injection (issue #5886 workaround)")
except (ImportError, AttributeError) as _patch_err:
    print(f"⚠️ Could not apply cache_breakpoint patch: {_patch_err}")

from app.config import settings

from app.tools.patient_tool import PatientRecordTool
from app.tools.routing_tool import DepartmentRoutingTool
from app.tools.appointment_tool import AppointmentTool
from app.tools.document_tool import DocumentTool
from app.tools.reminder_tool import ReminderTool
from app.tools.audit_tool import AuditLogTool
from app.tools.escalation_tool import EscalationTool

MISTRAL_AVAILABLE = bool(getattr(settings, "MISTRAL_API_KEY", None))
GROQ_AVAILABLE = bool(getattr(settings, "GROQ_API_KEY", None))

if MISTRAL_AVAILABLE:
    print("✅ Mistral API key configured")
else:
    print("⚠️ MISTRAL_API_KEY is not set in settings")

if GROQ_AVAILABLE:
    print("✅ Groq API key configured")
else:
    print("⚠️ GROQ_API_KEY is not set in settings")

# Cache the constructed+verified LLM at module level so it's built and
# connection-tested only ONCE per process, not on every incoming request.
# AgentCareCrew() / AgentCareAgents() gets instantiated fresh per request
# (see app/api/patients.py), so without this cache every single API call
# was paying for an extra "Test connection" round trip to the LLM provider.
_CACHED_LLM = None
_CACHED_MODEL_ID = None

class AgentCareAgents:
    """
    Creates all CrewAI agents for AgentCare.
    """

    def __init__(self):
        storage_dir = Path(settings.CREW_STORAGE_DIR).resolve()
        storage_dir.mkdir(parents=True, exist_ok=True)
        os.environ["CREWAI_STORAGE_DIR"] = str(storage_dir)

        self.llm = self._get_llm()

        # Shared tools
        self.audit_tool = AuditLogTool

        # Specialized tools
        self.patient_tool = PatientRecordTool
        self.routing_tool = DepartmentRoutingTool
        self.appointment_tool = AppointmentTool
        self.document_tool = DocumentTool
        self.reminder_tool = ReminderTool
        self.escalation_tool = EscalationTool

    @staticmethod
    def _get_llm():
        """
        Build (or reuse) the LLM client. The connection test only runs the
        first time this is called in the process; every subsequent request
        reuses the cached, already-verified LLM object.
        """
        global _CACHED_LLM, _CACHED_MODEL_ID

        if _CACHED_LLM is not None:
            return _CACHED_LLM

        # Determine which LLM provider to use based on availability and configuration
        if GROQ_AVAILABLE and settings.MODEL_PROVIDER.lower() == "groq":
            # Use Groq as the provider
            try:
                os.environ.setdefault("GROQ_API_KEY", settings.GROQ_API_KEY)
                model = settings.GROQ_MODEL
                model_id = model if model.startswith("groq/") else f"groq/{model}"
                llm = LLM(
                    model=model_id,
                    api_key=settings.GROQ_API_KEY,
                    drop_params=True,
                )
                # Test the connection ONCE (see cache note above).
                # NOTE: crewai.LLM has no .invoke() method (that's a LangChain
                # interface). CrewAI's LLM class uses .call() and expects a
                # list of message dicts, not a raw string.
                llm.call(messages=[{"role": "user", "content": "Test connection"}])
                print(f"🤖 Using Groq model via LiteLLM: {model_id} (drop_params=True)")
            except Exception as e:
                raise RuntimeError(
                    f"GROQ_API_KEY is not working properly. Error: {str(e)}. "
                    "Please check your Groq API key configuration."
                )
        elif MISTRAL_AVAILABLE:
            # Use Mistral as the provider (default fallback)
            try:
                os.environ.setdefault("MISTRAL_API_KEY", settings.MISTRAL_API_KEY)
                model = settings.MISTRAL_MODEL
                model_id = model if model.startswith("mistral/") else f"mistral/{model}"
                llm = LLM(
                    model=model_id,
                    api_key=settings.MISTRAL_API_KEY,
                    drop_params=True,
                )
                # Test the connection ONCE (see cache note above).
                llm.call(messages=[{"role": "user", "content": "Test connection"}])
                print(f"🤖 Using Mistral model via LiteLLM: {model_id} (drop_params=True)")
            except Exception as e:
                raise RuntimeError(
                    f"MISTRAL_API_KEY is not working properly. Error: {str(e)}. "
                    "Please check your Mistral API key configuration."
                )
        else:
            raise RuntimeError(
                "No valid LLM provider configured. "
                "Please set either MISTRAL_API_KEY or GROQ_API_KEY in your environment/.env file."
            )

        _CACHED_LLM = llm
        _CACHED_MODEL_ID = model_id
        return _CACHED_LLM

    def coordinator(self):
        return Agent(
            role="Healthcare Workflow Coordinator",
            goal=(
                "Coordinate a patient's administrative journey by "
                "understanding requests, delegating work to specialist agents, "
                "tracking workflow state, and ensuring completion."
            ),
            backstory=(
                "You are an experienced hospital operations coordinator. "
                "You specialize in administrative workflows such as patient "
                "registration, appointment scheduling, department routing, "
                "document coordination, reminders, and follow-ups. "
                "You never diagnose illnesses or provide treatment advice. "
                "Whenever a request appears medical or unsafe, you delegate "
                "to the Safety Agent."
            ),
            verbose=True,
            memory=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[self.patient_tool, self.audit_tool]
        )

    def routing_agent(self):
        return Agent(
            role="Department Routing Specialist",
            goal=(
                "Identify the correct hospital department for every "
                "administrative request while detecting emergency situations."
            ),
            backstory=(
                "You have years of experience at a hospital front desk. "
                "You understand every hospital department and know exactly "
                "where patients should be routed. "
                "If a patient requests diagnosis, prescriptions, or "
                "describes emergency symptoms, immediately escalate "
                "instead of attempting to answer."
            ),
            verbose=True,
            memory=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.routing_tool, self.escalation_tool, self.audit_tool]
        )

    def appointment_agent(self):
        return Agent(
            role="Appointment Scheduling Specialist",
            goal=(
                "Book, reschedule, cancel, and verify appointments "
                "without creating scheduling conflicts."
            ),
            backstory=(
                "You manage hospital schedules. "
                "You verify doctor availability, prevent double bookings, "
                "and keep appointment records synchronized with the database."
            ),
            verbose=True,
            memory=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.appointment_tool, self.audit_tool]
        )

    def document_agent(self):
        return Agent(
            role="Medical Document Coordinator",
            goal=(
                "Organize patient documents, classify uploaded files, "
                "detect duplicates, and identify missing required documents."
            ),
            backstory=(
                "You are responsible for maintaining clean and complete "
                "patient records. "
                "You classify ECG reports, blood reports, prescriptions, "
                "insurance documents, discharge summaries, and other "
                "medical records while avoiding duplicate uploads."
            ),
            verbose=True,
            memory=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.document_tool, self.audit_tool]
        )

    def safety_agent(self):
        return Agent(
            role="Healthcare Safety and Escalation Officer",
            goal=(
                "Ensure the system never provides diagnosis, "
                "prescriptions, dosage recommendations, or clinical advice. "
                "Generate reminders, follow-ups, and human escalations."
            ),
            backstory=(
                "You enforce hospital safety policies. "
                "You detect medical advice requests, emergencies, "
                "sensitive situations, and unauthorized actions. "
                "Whenever necessary, you escalate cases to hospital staff "
                "for human review."
            ),
            verbose=True,
            memory=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.reminder_tool, self.escalation_tool, self.audit_tool]
        )

    def all_agents(self):
        """
        Returns every agent in execution order.
        """
        return [
            self.coordinator(),
            self.routing_agent(),
            self.appointment_agent(),
            self.document_agent(),
            self.safety_agent(),
        ]

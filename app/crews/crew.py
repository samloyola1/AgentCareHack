# app/crews/crew.py

import os

from crewai import Crew, Process

from app.config import settings
from app.crews.agents import AgentCareAgents
from app.crews.tasks import AgentCareTasks


class AgentCareCrew:
    """
    Main CrewAI workflow for AgentCare.

    This class creates all agents, all tasks,
    and assembles the Crew.
    """

    def __init__(self):

        # Some CrewAI/embedchain internals read OPENAI_API_KEY from the
        # environment directly rather than from the embedder config dict,
        # so make sure it's set even though we also pass it explicitly below.
        if getattr(settings, "OPENAI_API_KEY", None):
            os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)

        # Initialize all agents
        self.agent_factory = AgentCareAgents()

        self.coordinator = self.agent_factory.coordinator()
        self.routing = self.agent_factory.routing_agent()
        self.appointment = self.agent_factory.appointment_agent()
        self.document = self.agent_factory.document_agent()
        self.safety = self.agent_factory.safety_agent()

        # Initialize tasks with the agent factory
        self.task_factory = AgentCareTasks(self.agent_factory)

    ####################################################################
    # Build Crew
    ####################################################################

    def build(self):
        """
        Creates and returns the CrewAI Crew.
        """

        crew = Crew(

            agents=[
                self.coordinator,
                self.routing,
                self.appointment,
                self.document,
                self.safety,
            ],

            tasks=[
                self.task_factory.registration_task(),
                self.task_factory.routing_task(),
                self.task_factory.appointment_task(),
                self.task_factory.document_task(),
                self.task_factory.safety_task(),
                self.task_factory.summary_task(),
            ],

            process=Process.sequential,

            verbose=True,

            # Memory needs an embedder to store/query memories. This is
            # SEPARATE from the LLM used for agent reasoning (Mistral/Groq).
            # Using OpenAI's embeddings here since that's the provider with
            # a working API key right now.
            memory=True,

            embedder={
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": settings.OPENAI_API_KEY,
                },
            },
        )

        return crew

    ####################################################################
    # Run Workflow
    ####################################################################

    def kickoff(self, patient_request: str):
        """
        Execute the complete workflow.

        Args:
            patient_request (str): Patient's administrative request.

        Returns:
            CrewAI Result
        """

        crew = self.build()

        result = crew.kickoff(
            inputs={
                "patient_request": patient_request
            }
        )

        return result
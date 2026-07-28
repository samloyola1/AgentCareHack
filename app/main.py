"""
AgentCare - Main FastAPI Application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, check_database, engine

# ----------------------------------------------------
# Import API Routers
# ----------------------------------------------------

from app.api import (
    auth,
    patients,
    appointments,
    documents,
    reminders,
    staff,
)

# ----------------------------------------------------
# Create Database Tables
# ----------------------------------------------------

Base.metadata.create_all(bind=engine)

# ----------------------------------------------------
# Application Lifespan
# ----------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("AgentCare API Started")
    print("=" * 60)

    yield

    print("=" * 60)
    print("AgentCare API Shutdown")
    print("=" * 60)

# ----------------------------------------------------
# FastAPI App
# ----------------------------------------------------

app = FastAPI(
    title="AgentCare API",
    description="""
AgentCare is an AI-powered healthcare administration platform.

Features:
- Patient Registration
- Department Routing
- Appointment Booking
- Document Management
- Reminder Scheduling
- Human Escalation
- Audit Logging
- CrewAI Multi-Agent Workflow
""",
    version="1.0.0",
    lifespan=lifespan,
)

# ----------------------------------------------------
# CORS
# ----------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Include API Routers
# ----------------------------------------------------

app.include_router(patients.router)
app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(documents.router)
app.include_router(reminders.router)
app.include_router(staff.router)

# ----------------------------------------------------
# Root Endpoint
# ----------------------------------------------------

@app.get("/")
def root():
    return {
        "application": "AgentCare",
        "version": "1.0.0",
        "status": "Running",
        "docs": "/docs",
        "health": "/health",
    }

# ----------------------------------------------------
# Health Check
# ----------------------------------------------------

@app.get("/health")
def health():
    db_ok = check_database()

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "service": "AgentCare API",
        "llm_provider": settings.MODEL_PROVIDER,
        "llm_model": settings.MISTRAL_MODEL if settings.MODEL_PROVIDER.lower() == "mistral" else settings.GROQ_MODEL,
    }

# ----------------------------------------------------
# Application Information
# ----------------------------------------------------

@app.get("/info")
def info():
    return {
        "project": "AgentCare",
        "framework": "FastAPI",
        "agents": [
            "Coordinator Agent",
            "Department Routing Agent",
            "Appointment Agent",
            "Document Agent",
            "Follow-up Agent",
            "Safety Agent",
        ],
        "database": "SQLite / PostgreSQL",
        "llm_framework": "CrewAI",
        "llm_provider": settings.MODEL_PROVIDER,
        "llm_model": settings.MISTRAL_MODEL if settings.MODEL_PROVIDER.lower() == "mistral" else settings.GROQ_MODEL,
    }
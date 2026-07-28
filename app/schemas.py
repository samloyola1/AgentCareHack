"""
Pydantic Schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ==========================================================
# Authentication Schemas
# ==========================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


# ==========================================================
# User Schemas
# ==========================================================

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "patient"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Patient Schemas
# ==========================================================

class PatientBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    date_of_birth: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact: Optional[str] = None


class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Patient Administrative Request
# ==========================================================

class PatientRequest(BaseModel):
    patient_id: int
    request: str


class PatientRequestResponse(BaseModel):
    workflow_id: int
    status: str
    crew_result: str


# ==========================================================
# Common Response Schemas
# ==========================================================

class MessageResponse(BaseModel):
    success: bool
    message: str


class ErrorResponse(BaseModel):
    detail: str


# ==========================================================
# Health Check Schema
# ==========================================================

class HealthResponse(BaseModel):
    status: str
    service: str

# ==========================================================
# Department Schemas
# ==========================================================

class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Doctor Schemas
# ==========================================================

class DoctorBase(BaseModel):
    department_id: int
    name: str
    specialization: Optional[str] = None
    active: bool = True


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    department_id: Optional[int] = None
    name: Optional[str] = None
    specialization: Optional[str] = None
    active: Optional[bool] = None


class DoctorResponse(DoctorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Appointment Slot Schemas
# ==========================================================

class AppointmentSlotBase(BaseModel):
    doctor_id: int
    start_time: datetime
    end_time: datetime
    status: str = "Available"


class AppointmentSlotCreate(AppointmentSlotBase):
    pass


class AppointmentSlotUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None


class AppointmentSlotResponse(AppointmentSlotBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Appointment Schemas
# ==========================================================

class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    slot_id: int
    reason: str
    status: str = "Booked"


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    doctor_id: Optional[int] = None
    slot_id: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Appointment Search / Booking
# ==========================================================

class AppointmentBookingRequest(BaseModel):
    patient_id: int
    department_id: int
    preferred_date: datetime
    reason: str


class AppointmentBookingResponse(BaseModel):
    success: bool
    appointment_id: Optional[int] = None
    doctor_name: Optional[str] = None
    appointment_time: Optional[datetime] = None
    message: str


class AppointmentRescheduleRequest(BaseModel):
    appointment_id: int
    new_slot_id: int


class AppointmentCancelRequest(BaseModel):
    appointment_id: int
    reason: Optional[str] = None


# Backwards-compatible names used by the appointments router.
AppointmentRequest = AppointmentBookingRequest
RescheduleRequest = AppointmentRescheduleRequest
CancelRequest = AppointmentCancelRequest


# ==========================================================
# Patient Document Schemas
# ==========================================================

class PatientDocumentBase(BaseModel):
    patient_id: int
    document_type: str
    file_path: str
    checksum: str
    document_date: Optional[datetime] = None


class PatientDocumentCreate(PatientDocumentBase):
    pass


class PatientDocumentUpdate(BaseModel):
    document_type: Optional[str] = None
    file_path: Optional[str] = None


class PatientDocumentResponse(PatientDocumentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Workflow Schemas
# ==========================================================

class WorkflowRunBase(BaseModel):
    patient_id: int
    current_step: str
    state: str
    status: str


class WorkflowRunCreate(WorkflowRunBase):
    pass


class WorkflowRunUpdate(BaseModel):
    current_step: Optional[str] = None
    state: Optional[str] = None
    status: Optional[str] = None


class WorkflowRunResponse(WorkflowRunBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Reminder Schemas
# ==========================================================

class ReminderBase(BaseModel):
    patient_id: int
    appointment_id: int
    reminder_type: str
    scheduled_at: datetime
    status: str = "Pending"


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    reminder_type: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None


class ReminderResponse(ReminderBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Escalation Schemas
# ==========================================================

class EscalationBase(BaseModel):
    workflow_run_id: int
    reason: str
    status: str = "Pending"
    reviewed_by: Optional[int] = None


class EscalationCreate(EscalationBase):
    pass


class EscalationUpdate(BaseModel):
    reason: Optional[str] = None
    status: Optional[str] = None
    reviewed_by: Optional[int] = None


class EscalationResponse(EscalationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Audit Event Schemas
# ==========================================================

class AuditEventBase(BaseModel):
    actor_id: int
    action: str
    entity_type: str
    entity_id: int
    metadata: Optional[str] = None


class AuditEventCreate(AuditEventBase):
    pass


class AuditEventResponse(AuditEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Dashboard Schemas
# ==========================================================

class DashboardStats(BaseModel):
    total_patients: int
    total_appointments: int
    total_documents: int
    total_workflows: int
    total_escalations: int
    pending_reminders: int


# ==========================================================
# Notification Schema
# ==========================================================

class NotificationResponse(BaseModel):
    success: bool
    message: str


# ==========================================================
# Generic API Response
# ==========================================================

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

"""
Application Configuration

Loads configuration from environment variables and .env file.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =====================================================
    # Application
    # =====================================================

    APP_NAME: str = "AgentCare"

    APP_VERSION: str = "1.0.0"

    DEBUG: bool = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_mode(cls, value: object) -> object:
        """Accept common deployment labels as well as boolean values."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"development", "dev", "debug"}:
                return True
            if normalized in {"production", "prod", "release"}:
                return False
        return value

    SECRET_KEY: str = "change-this-secret-key"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # =====================================================
    # Database
    # =====================================================

    DATABASE_URL: str = "sqlite:///./agentcare.db"

    # =====================================================
    # LLM Configuration
    # =====================================================

    MODEL_PROVIDER: str = "mistral"

    # =====================================================
    # Mistral / LLM
    # =====================================================

    MISTRAL_API_KEY: str = ""

    MISTRAL_MODEL: str = "open-mistral-7b"


    # =====================================================
    # Groq / LLM
    # =====================================================

    GROQ_API_KEY: str = ""

    GROQ_MODEL: str = "openai/gpt-oss-120b"


    # =====================================================
    # Groq / LLM
    # =====================================================

    OPENAI_API_KEY: str = ""


    # =====================================================
    # CrewAI
    # =====================================================

    CREW_VERBOSE: bool = True

    CREW_MEMORY: bool = True

    CREW_STORAGE_DIR: str = "data/crewai"

    # =====================================================
    # File Uploads
    # =====================================================

    UPLOAD_DIRECTORY: str = "uploads"

    MAX_UPLOAD_SIZE_MB: int = 10

    ALLOWED_EXTENSIONS: list[str] = [
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "doc",
        "docx",
    ]

    # =====================================================
    # Email
    # =====================================================

    ENABLE_EMAIL: bool = False

    SMTP_SERVER: str = "smtp.gmail.com"

    SMTP_PORT: int = 587

    EMAIL_USERNAME: str = ""

    EMAIL_PASSWORD: str = ""

    SENDER_EMAIL: str = ""

    # =====================================================
    # Notifications
    # =====================================================

    REMINDER_HOURS_BEFORE: int = 24

    FOLLOWUP_DAYS_AFTER: int = 30

    # =====================================================
    # Logging
    # =====================================================

    LOG_LEVEL: str = "INFO"

    LOG_FILE: str = "logs/agentcare.log"

    # =====================================================
    # Security
    # =====================================================

    PASSWORD_MIN_LENGTH: int = 8

    ENABLE_REGISTRATION: bool = True

    # =====================================================
    # Environment Configuration
    # =====================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

"""
Database Configuration
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings


# ==========================================================
# Database Engine
# ==========================================================

DATABASE_URL = settings.DATABASE_URL

# SQLite requires this option
connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# ==========================================================
# Session Factory
# ==========================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ==========================================================
# Base Model
# ==========================================================

Base = declarative_base()


# ==========================================================
# Dependency for FastAPI
# ==========================================================

def get_db():
    """
    FastAPI database dependency.

    Usage:
        db: Session = Depends(get_db)
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==========================================================
# Database Initialization
# ==========================================================

def init_db():
    """
    Create all database tables.
    """

    Base.metadata.create_all(bind=engine)


# ==========================================================
# Drop Database Tables (Development Only)
# ==========================================================

def drop_db():
    """
    Drop all database tables.

    WARNING:
    Only use in development/testing.
    """

    Base.metadata.drop_all(bind=engine)


# ==========================================================
# Database Health Check
# ==========================================================

def check_database():
    """
    Returns True if database connection is successful.
    """

    try:

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception as e:

        print(f"Database Error: {e}")

        return False
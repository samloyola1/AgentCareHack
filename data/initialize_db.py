"""
Initialize the AgentCare database with sample data.

Usage:
    python data/initialize_db.py
"""

import json
import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Department, Doctor, User


DATA_DIR = Path(__file__).parent


def load_json(filename: str):
    """Load a JSON file from the data directory."""
    path = DATA_DIR / filename

    if not path.exists():
        print(f"⚠ File not found: {filename}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.\n")


def seed_departments(db):
    """Insert departments."""
    departments = load_json("departments.json")

    count = 0

    for dept in departments:

        existing = (
            db.query(Department)
            .filter(Department.name == dept["name"])
            .first()
        )

        if existing:
            continue

        db.add(
            Department(
                name=dept["name"],
                description=dept.get("description", ""),
            )
        )

        count += 1

    db.commit()

    print(f"Seeded {count} departments.")


def seed_doctors(db):
    """Insert doctors."""
    doctors = load_json("doctors.json")

    count = 0

    for doctor in doctors:

        department = (
            db.query(Department)
            .filter(
                Department.name == doctor["department"]
            )
            .first()
        )

        if not department:
            print(
                f"Department '{doctor['department']}' not found."
            )
            continue

        existing = (
            db.query(Doctor)
            .filter(
                Doctor.name == doctor["name"]
            )
            .first()
        )

        if existing:
            continue

        db.add(
            Doctor(
                name=doctor["name"],
                specialization=doctor.get(
                    "specialization",
                    "",
                ),
                department_id=department.id,
                active=True,
            )
        )

        count += 1

    db.commit()

    print(f"Seeded {count} doctors.")


def seed_users(db):
    """Insert admin/staff users."""
    users = load_json("users.json")

    count = 0

    for user in users:

        existing = (
            db.query(User)
            .filter(User.email == user["email"])
            .first()
        )

        if existing:
            continue

        db.add(
            User(
                name=user["name"],
                email=user["email"],
                password_hash=hash_password(
                    user["password"]
                ),
                role=user["role"],
                active=True,
            )
        )

        count += 1

    db.commit()

    print(f"Seeded {count} users.")


def initialize():
    """Initialize the database."""

    create_tables()

    db = SessionLocal()

    try:

        seed_departments(db)

        seed_doctors(db)

        seed_users(db)

        print("\n===================================")
        print("AgentCare database initialized.")
        print("===================================")

    finally:
        db.close()


if __name__ == "__main__":
    initialize()
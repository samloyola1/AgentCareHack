import json
import re
from crewai.tools import tool


# Department keywords
DEPARTMENT_KEYWORDS = {
    "Cardiology": [
        "heart",
        "cardiology",
        "ecg",
        "chest pain",
        "palpitations",
        "blood pressure",
    ],
    "Neurology": [
        "brain",
        "neurology",
        "headache",
        "migraine",
        "stroke",
        "seizure",
    ],
    "Orthopedics": [
        "bone",
        "fracture",
        "joint",
        "knee",
        "hip",
        "back pain",
        "orthopedic",
    ],
    "Dermatology": [
        "skin",
        "rash",
        "itching",
        "eczema",
        "psoriasis",
    ],
    "ENT": [
        "ear",
        "nose",
        "throat",
        "sinus",
        "hearing",
    ],
    "Pediatrics": [
        "child",
        "kid",
        "baby",
        "infant",
        "pediatric",
    ],
    "General Medicine": [
        "fever",
        "cold",
        "cough",
        "checkup",
        "general",
    ],
}


# Emergency keywords
EMERGENCY_KEYWORDS = [
    "heart attack",
    "stroke",
    "difficulty breathing",
    "can't breathe",
    "unconscious",
    "severe bleeding",
    "chest pain",
    "suicidal",
    "collapse",
    "emergency",
]


# Medical advice keywords
MEDICAL_ADVICE_KEYWORDS = [
    "diagnose",
    "diagnosis",
    "prescribe",
    "medicine",
    "medication",
    "dosage",
    "dose",
    "treatment",
    "what medicine",
    "increase my insulin",
]


@tool("Department Routing Tool")
def DepartmentRoutingTool(patient_request: str):
    """
    Determine the correct hospital department for an
    administrative request.

    Detect emergencies and requests for medical advice.
    """

    request = patient_request.lower()

    # -------------------------------------------------
    # Emergency Detection
    # -------------------------------------------------

    for keyword in EMERGENCY_KEYWORDS:
        if keyword in request:

            return json.dumps(
                {
                    "intent": "Emergency",
                    "department": None,
                    "confidence": 100,
                    "escalation_required": True,
                    "reason": "Emergency symptoms detected.",
                },
                indent=4,
            )

    # -------------------------------------------------
    # Medical Advice Detection
    # -------------------------------------------------

    for keyword in MEDICAL_ADVICE_KEYWORDS:
        if keyword in request:

            return json.dumps(
                {
                    "intent": "Medical Advice",
                    "department": None,
                    "confidence": 100,
                    "escalation_required": True,
                    "reason": "Medical advice requests must be reviewed by a clinician.",
                },
                indent=4,
            )

    # -------------------------------------------------
    # Department Classification
    # -------------------------------------------------

    best_department = "General Medicine"
    score = 0

    for department, keywords in DEPARTMENT_KEYWORDS.items():

        matches = 0

        for keyword in keywords:

            if re.search(rf"\b{re.escape(keyword)}\b", request):
                matches += 1

        if matches > score:
            score = matches
            best_department = department

    confidence = min(60 + score * 10, 99)

    return json.dumps(
        {
            "intent": "Administrative Appointment Request",
            "department": best_department,
            "confidence": confidence,
            "escalation_required": False,
            "reason": None,
        },
        indent=4,
    )
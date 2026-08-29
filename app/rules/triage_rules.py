from dataclasses import dataclass
from typing import Literal


RiskLevel = Literal[
    "NORMAL",
    "URGENT",
    "EMERGENCY",
]


@dataclass(frozen=True)
class SymptomRule:
    code: str
    symptoms: frozenset[str]
    risk_level: RiskLevel
    description: str


# IMPORTANT:
# These are prototype rules.
# Final clinical thresholds/mappings must be
# validated by qualified clinicians.


EMERGENCY_SYMPTOM_RULES = [
    SymptomRule(
        code="SEVERE_CHEST_PAIN",
        symptoms=frozenset({
            "severe chest pain",
        }),
        risk_level="EMERGENCY",
        description="Severe chest pain reported.",
    ),

    SymptomRule(
        code="LOSS_OF_CONSCIOUSNESS",
        symptoms=frozenset({
            "unconsciousness",
            "loss of consciousness",
        }),
        risk_level="EMERGENCY",
        description="Loss of consciousness reported.",
    ),

    SymptomRule(
        code="SEVERE_BREATHING_DIFFICULTY",
        symptoms=frozenset({
            "severe breathing difficulty",
        }),
        risk_level="EMERGENCY",
        description="Severe breathing difficulty reported.",
    ),

    SymptomRule(
        code="SEIZURE",
        symptoms=frozenset({
            "seizure",
        }),
        risk_level="EMERGENCY",
        description="Seizure reported.",
    ),

    SymptomRule(
        code="SEVERE_BLEEDING",
        symptoms=frozenset({
            "severe bleeding",
        }),
        risk_level="EMERGENCY",
        description="Severe bleeding reported.",
    ),
]


URGENT_SYMPTOM_RULES = [
    SymptomRule(
        code="BREATHING_DIFFICULTY",
        symptoms=frozenset({
            "difficulty breathing",
            "shortness of breath",
        }),
        risk_level="URGENT",
        description="Breathing difficulty reported.",
    ),

    SymptomRule(
        code="PERSISTENT_VOMITING",
        symptoms=frozenset({
            "persistent vomiting",
        }),
        risk_level="URGENT",
        description="Persistent vomiting reported.",
    ),

    SymptomRule(
        code="SEVERE_ABDOMINAL_PAIN",
        symptoms=frozenset({
            "severe abdominal pain",
        }),
        risk_level="URGENT",
        description="Severe abdominal pain reported.",
    ),

    SymptomRule(
        code="CONFUSION",
        symptoms=frozenset({
            "confusion",
        }),
        risk_level="URGENT",
        description="Confusion reported.",
    ),
]


SPECIALTY_MAPPING = {
    "chest pain": "cardiology",
    "severe chest pain": "cardiology",
    "palpitations": "cardiology",

    "eye pain": "ophthalmology",
    "vision problems": "ophthalmology",

    "ear pain": "ent",
    "hearing problems": "ent",

    "skin rash": "dermatology",

    "joint pain": "orthopedics",

    "pregnancy": "gynecology",

    "fever": "general_medicine",
    "cough": "general_medicine",
    "headache": "general_medicine",
    "body ache": "general_medicine",
}
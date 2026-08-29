from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal[
    "mild",
    "moderate",
    "severe",
    "unknown",
]

Onset = Literal[
    "sudden",
    "gradual",
    "unknown",
]

Progression = Literal[
    "improving",
    "stable",
    "worsening",
    "persistent",
    "unknown",
]


class Symptom(BaseModel):
    name: str = Field(min_length=1)
    duration: str | None = None
    severity: Severity = "unknown"
    onset: Onset = "unknown"
    progression: Progression = "unknown"


class Vitals(BaseModel):
    temperature_c: float | None = Field(
        default=None,
        ge=30,
        le=45,
    )

    heart_rate: int | None = Field(
        default=None,
        ge=20,
        le=250,
    )

    respiratory_rate: int | None = Field(
        default=None,
        ge=5,
        le=80,
    )

    spo2: int | None = Field(
        default=None,
        ge=50,
        le=100,
    )

    systolic_bp: int | None = Field(
        default=None,
        ge=50,
        le=250,
    )

    diastolic_bp: int | None = Field(
        default=None,
        ge=30,
        le=150,
    )


class MedicalHistory(BaseModel):
    chronic_conditions: list[str] = Field(
        default_factory=list
    )

    medications: list[str] = Field(
        default_factory=list
    )

    allergies: list[str] = Field(
        default_factory=list
    )


class TriageRequest(BaseModel):
    age: int = Field(
        ge=0,
        le=120,
    )

    sex: Literal[
        "male",
        "female",
        "other",
        "unknown",
    ] = "unknown"

    chief_complaint: str | None = None

    symptoms: list[Symptom] = Field(
        default_factory=list
    )

    vitals: Vitals | None = None

    medical_history: MedicalHistory = Field(
        default_factory=MedicalHistory
    )

    pregnancy: bool = False


class TriageAnalyzeRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="Patient's message"
    )

    language: str | None = Field(
        default=None,
        description="Patient language, e.g. hi, en"
    )

    age: int = Field(
        ge=0,
        le=120,
    )

    sex: Literal[
        "male",
        "female",
        "other",
        "unknown",
    ] = "unknown"

    pregnancy: bool = False

    vitals: Vitals | None = None

    medical_history: MedicalHistory = Field(
        default_factory=MedicalHistory
    )


class RedFlag(BaseModel):
    code: str
    description: str
    source: Literal[
        "symptom",
        "vital",
        "history",
        "special_condition",
    ]


class DecisionReason(BaseModel):
    code: str
    description: str


class TriageResponse(BaseModel):
    risk_level: Literal[
        "NORMAL",
        "URGENT",
        "EMERGENCY",
    ]

    priority: Literal[
        "ROUTINE",
        "HIGH",
        "CRITICAL",
    ]

    red_flags: list[RedFlag]

    decision_reasons: list[DecisionReason]

    recommended_action: str

    suggested_specialty: str | None = None

    requires_escalation: bool

    missing_information: list[str] = Field(
        default_factory=list
    )
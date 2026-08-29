from pydantic import BaseModel, Field


class ExtractedSymptom(BaseModel):
    name: str = Field(min_length=1)

    duration: str | None = None

    severity: str = "unknown"

    onset: str = "unknown"

    progression: str = "unknown"


class TriageExtractionRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="Patient's message in natural language",
    )

    language: str | None = Field(
        default=None,
        description="Optional language hint such as hi, en, bho, mai",
    )


class TriageExtractionResponse(BaseModel):
    symptoms: list[ExtractedSymptom]

    chief_complaint: str | None = None

    language: str

    missing_information: list[str] = Field(
        default_factory=list
    )
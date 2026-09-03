from pydantic import BaseModel, Field
from typing import Optional


class PrescriptionRequest(BaseModel):
    appointmentId: str
    prescriptionText: str = Field(..., min_length=1)


class Medicine(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None


class PrescriptionResponse(BaseModel):

    appointmentId: str

    patientId: Optional[str] = None
    doctorId: Optional[str] = None

    complaints: list[str] = []

    diagnosis: list[str] = []

    medicines: list[Medicine] = []

    tests: list[str] = []

    advice: Optional[str] = None

    followUpDate: Optional[str] = None
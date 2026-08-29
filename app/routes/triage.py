from fastapi import APIRouter

from app.schemas.triage import (
    TriageAnalyzeRequest,
    TriageRequest,
    TriageResponse,
)

from app.schemas.triage_extraction import (
    TriageExtractionRequest,
    TriageExtractionResponse,
)

from app.services.triage_service import (
    analyze_patient,
    triage_patient,
)

from app.services.triage_extraction_service import (
    extract_patient_information,
)


router = APIRouter(
    prefix="/api/triage",
    tags=["Triage"],
)


@router.post(
    "",
    response_model=TriageResponse,
)
async def run_triage(
    request: TriageRequest,
):
    return triage_patient(request)


@router.post(
    "/extract",
    response_model=TriageExtractionResponse,
)
async def extract_triage_information(
    request: TriageExtractionRequest,
):
    return extract_patient_information(request)


@router.post(
    "/analyze",
    response_model=TriageResponse,
)
async def analyze_triage(
    request: TriageAnalyzeRequest,
):
    return analyze_patient(request)
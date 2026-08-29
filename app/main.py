from dotenv import load_dotenv
from fastapi import FastAPI

from app.routes.prescription import router as prescription_router
from app.routes.triage import router as triage_router


load_dotenv()


app = FastAPI(
    title="Prescription AI Service",
    description="AI service for prescription processing and patient triage",
    version="1.0.0",
)


app.include_router(prescription_router)
app.include_router(triage_router)


@app.get("/")
async def root():
    return {
        "message": "Prescription AI Service is running"
    }
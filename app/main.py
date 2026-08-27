from fastapi import FastAPI

from app.routes.prescription import router as prescription_router


app = FastAPI(
    title="Prescription AI Service",
    description="AI service for converting doctor prescription text into structured data",
    version="1.0.0",
)


app.include_router(prescription_router)


@app.get("/")
async def root():
    return {
        "message": "Prescription AI Service is running"
    }
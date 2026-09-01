from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.prescription import router as prescription_router
from app.routes.triage import router as triage_router


app = FastAPI(
    title="Prescription AI Service",
    description="AI service for prescription processing and patient triage",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        # "https://your-frontend-domain.com",  # production frontend ke liye
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prescription_router)
app.include_router(triage_router)


@app.get("/")
async def root():
    return {
        "message": "Prescription AI Service is running"
    }

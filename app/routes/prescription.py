import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.prescription import (
    PrescriptionRequest,
    PrescriptionResponse,
)

from app.services.prescription_ocr import extract_text_from_image

# ============================================================
# LLM PRESCRIPTION PARSER
# ============================================================

from app.services.prescription_parser import (
    parse_prescription as parse_prescription_service
)


router = APIRouter(
    prefix="/api/prescription",
    tags=["Prescription"],
)


# ============================================================
# TEXT PARSE
# ============================================================

@router.post("/parse", response_model=PrescriptionResponse)
async def parse_prescription_endpoint(
    request: PrescriptionRequest
):
    return await parse_prescription_service(
        appointment_id=request.appointmentId,
        prescription_text=request.prescriptionText,
    )


# ============================================================
# OCR
# ============================================================

@router.post("/ocr")
async def ocr_prescription(
    file: UploadFile = File(...)
):
    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="File type could not be determined."
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed."
        )

    # --------------------------------------------------------
    # Read uploaded image
    # --------------------------------------------------------

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    # --------------------------------------------------------
    # Save temporarily
    # --------------------------------------------------------

    suffix = os.path.splitext(file.filename or "")[1]

    if not suffix:
        suffix = ".jpg"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(image_bytes)
            temp_path = temp_file.name

        # ----------------------------------------------------
        # Run existing OCR
        # ----------------------------------------------------

        result = await extract_text_from_image(temp_path)

        return result

    except Exception as e:

        print("\n--- OCR API ERROR ---")
        print(type(e).__name__)
        print(str(e))
        print("--- END OCR API ERROR ---\n")

        raise HTTPException(
            status_code=500,
            detail=f"OCR failed: {str(e)}"
        )

    finally:

        # ----------------------------------------------------
        # Delete temporary file
        # ----------------------------------------------------

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


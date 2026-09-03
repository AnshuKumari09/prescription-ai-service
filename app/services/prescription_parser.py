import os
import json

from dotenv import load_dotenv
from groq import AsyncGroq

from app.schemas.prescription import PrescriptionResponse


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# GROQ CLIENT
# ============================================================

client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)


MODEL = os.getenv(
    "GROQ_MODEL",
    "qwen/qwen3.8-27b"
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a medical prescription information extraction system.

Extract ONLY information explicitly present in the prescription.

Do NOT:
- diagnose the patient
- add medicines
- add tests
- invent missing information
- infer information that is not explicitly written

Extract:
1. complaints
2. diagnosis
3. medicines
4. tests
5. advice
6. follow-up date

For every medicine extract:
- name
- dosage
- frequency
- duration
- instructions

Preserve prescription abbreviations such as:
OD, BD, TDS, QID, HS, SOS, etc.

If a field is not present, return an empty list or null.

If the prescription says something like
"follow up after 5 days", do NOT invent a calendar date.
Return null for followUpDate unless an actual date is explicitly present.

Return ONLY valid JSON.

The JSON MUST follow this exact structure:

{
  "appointmentId": "",
  "patientId": null,
  "doctorId": null,
  "complaints": [],
  "diagnosis": [],
  "medicines": [
    {
      "name": "",
      "dosage": "",
      "frequency": "",
      "duration": "",
      "instructions": ""
    }
  ],
  "tests": [],
  "advice": "",
  "followUpDate": null
}
Important:
- appointmentId MUST be included.
- patientId MUST be included and should be null if not explicitly available.
- doctorId MUST be included and should be null if not explicitly available.
- complaints MUST be an array of strings.
- diagnosis MUST be an array of strings.
- tests MUST be an array of strings.
- advice MUST be a string.
- medicines MUST be an array of objects.
- followUpDate MUST be null unless an actual date is explicitly present.
"""


# ============================================================
# PARSE PRESCRIPTION
# ============================================================

async def parse_prescription(
    appointment_id: str,
    prescription_text: str,
) -> PrescriptionResponse:

    print(
        "🔥🔥🔥 PARSE_PRESCRIPTION CALLED 🔥🔥🔥",
        flush=True
    )

    print(
        "APPOINTMENT:",
        appointment_id,
        flush=True
    )

    print(
        "PRESCRIPTION TEXT:",
        prescription_text,
        flush=True
    )

    # --------------------------------------------------------
    # Call Groq LLM
    # --------------------------------------------------------

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prescription_text,
            },
        ],
        temperature=0,
        response_format={
            "type": "json_object"
        },
    )

    # --------------------------------------------------------
    # Get LLM response
    # --------------------------------------------------------

    content = response.choices[0].message.content

    print(
        "LLM RESPONSE:",
        content,
        flush=True
    )

    # --------------------------------------------------------
    # Convert JSON string → Python dictionary
    # --------------------------------------------------------

    data = json.loads(content)

    # --------------------------------------------------------
    # Add appointment ID from API request
    # --------------------------------------------------------

    data["appointmentId"] = appointment_id

    # --------------------------------------------------------
    # Validate against Pydantic schema
    # --------------------------------------------------------

    result = PrescriptionResponse.model_validate(data)

    # --------------------------------------------------------
    # Return validated response
    # --------------------------------------------------------

    return result
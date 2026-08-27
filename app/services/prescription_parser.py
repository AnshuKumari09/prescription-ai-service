import os

from dotenv import load_dotenv
from groq import AsyncGroq

from app.schemas.prescription import PrescriptionResponse

load_dotenv()

client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


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
"""


async def parse_prescription(
    appointment_id: str,
    prescription_text: str,
) -> PrescriptionResponse:

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

    content = response.choices[0].message.content

    result = PrescriptionResponse.model_validate_json(content)

    return result.model_copy(
        update={
            "appointmentId": appointment_id
        }
    )
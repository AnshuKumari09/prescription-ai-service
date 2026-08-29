import json
import os

from groq import Groq

from app.schemas.triage_extraction import (
    ExtractedSymptom,
    TriageExtractionRequest,
    TriageExtractionResponse,
)


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


SYSTEM_PROMPT = """
You are a medical symptom information extraction system.

Your job is ONLY to extract information from a patient's message.

You MUST NOT:
- diagnose diseases
- prescribe medicines
- recommend treatment
- make emergency decisions
- invent symptoms
- infer symptoms that the patient did not mention

Extract only information explicitly stated or clearly expressed
by the patient.

Normalize symptoms into simple canonical English names.

Examples:

"bukhar" -> "fever"
"khansi" -> "cough"
"sar dard" -> "headache"
"saans phool rahi hai" -> "difficulty breathing"
"pet me dard" -> "abdominal pain"
"ulti" -> "vomiting"

For each symptom extract:

- name
- duration
- severity
- onset
- progression

If information is not available, use "unknown".

Also extract the main complaint.

Return ONLY valid JSON.

JSON format:

{
  "symptoms": [
    {
      "name": "fever",
      "duration": "3 days",
      "severity": "moderate",
      "onset": "gradual",
      "progression": "persistent"
    }
  ],
  "chief_complaint": "fever",
  "language": "hi",
  "missing_information": []
}

Do not include markdown.
Do not include explanations.
"""


def extract_patient_information(
    request: TriageExtractionRequest,
) -> TriageExtractionResponse:

    user_prompt = f"""
Patient message:

{request.message}

Language hint:

{request.language or "unknown"}

Extract the clinically relevant symptoms and information.
Return JSON only.
"""

    response = client.chat.completions.create(
        model=os.getenv("GROQ_TEXT_MODEL"),
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0,
        response_format={
            "type": "json_object"
        },
    )

    raw_output = response.choices[0].message.content

    if not raw_output:
        raise ValueError(
            "LLM returned an empty response"
        )

    try:
        data = json.loads(raw_output)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM returned invalid JSON"
        ) from exc

    symptoms = [
        ExtractedSymptom(**symptom)
        for symptom in data.get("symptoms", [])
    ]

    return TriageExtractionResponse(
        symptoms=symptoms,
        chief_complaint=data.get(
            "chief_complaint"
        ),
        language=data.get(
            "language",
            request.language or "unknown",
        ),
        missing_information=data.get(
            "missing_information",
            [],
        ),
    )
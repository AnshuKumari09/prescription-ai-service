import os
import base64
import json
import re
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from groq import AsyncGroq


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set in the environment."
    )


# ============================================================
# GROQ CLIENT
# ============================================================

client = AsyncGroq(
    api_key=GROQ_API_KEY
)


VISION_MODEL = os.getenv(
    "GROQ_VISION_MODEL",
    "qwen/qwen3.6-27b"
)


# ============================================================
# IMAGE ENCODING
# ============================================================

def encode_image(image_path: str) -> str:
    """
    Convert prescription image to base64.
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image file not found: {image_path}"
        )

    with open(image_path, "rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


# ============================================================
# JSON PARSER
# ============================================================

def parse_json_response(
    raw_text: str,
) -> dict[str, Any]:

    if not raw_text:
        raise ValueError(
            "Model returned an empty response."
        )

    raw_text = raw_text.strip()

    print("\n--- RAW MODEL OUTPUT ---")
    print(raw_text)
    print("--- END RAW MODEL OUTPUT ---\n")

    # --------------------------------------------------------
    # Remove <think> blocks if model ever returns them
    # --------------------------------------------------------

    raw_text = re.sub(
        r"<think>.*?</think>",
        "",
        raw_text,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()

    raw_text = re.sub(
        r"</?think>",
        "",
        raw_text,
        flags=re.IGNORECASE,
    ).strip()

    # --------------------------------------------------------
    # Remove markdown fences
    # --------------------------------------------------------

    raw_text = re.sub(
        r"```json\s*",
        "",
        raw_text,
        flags=re.IGNORECASE,
    )

    raw_text = re.sub(
        r"```\s*",
        "",
        raw_text,
    ).strip()

    # --------------------------------------------------------
    # Find JSON object
    # --------------------------------------------------------

    start = raw_text.find("{")
    end = raw_text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "Model did not return a valid JSON object.\n\n"
            f"Cleaned model output:\n{raw_text}"
        )

    json_text = raw_text[start:end + 1]

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:
        result = json.loads(json_text)

    except json.JSONDecodeError as e:

        print("Invalid JSON returned by model:")
        print(json_text)

        print("\nJSON error:")
        print(e)

        raise ValueError(
            "Model returned invalid JSON."
        ) from e

    if not isinstance(result, dict):
        raise ValueError(
            "Model JSON response is not an object."
        )

    return result


# ============================================================
# OCR PROMPT
# ============================================================
OCR_PROMPT = r"""
You are an expert medical-prescription handwriting recognition engine.

Your task is to read a handwritten medical prescription and convert it
into the required JSON structure.

You have TWO responsibilities:

1. VISUAL READING
   Carefully inspect the actual handwriting, characters, numbers,
   abbreviations, symbols, spacing, and their position on the prescription.

2. MEDICAL CONTEXT RECOGNITION
   Use knowledge of common medical prescription-writing conventions,
   common doctor handwriting patterns, common prescription abbreviations,
   medicine naming patterns, dosage patterns, and clinical context to
   understand what the handwriting most likely represents.

IMPORTANT:
You are NOT merely doing generic OCR.

A human doctor/pharmacist does not read every handwritten character
independently. They combine:
- handwriting appearance
- surrounding letters
- prescription layout
- medical abbreviations
- medicine naming conventions
- dosage/strength patterns
- frequency
- nearby clinical information

You must use the same reasoning approach.

============================================================
MOST IMPORTANT RULE
============================================================

DO NOT BLINDLY TRUST RAW CHARACTER OCR.

Handwritten medical text often produces visually incorrect OCR such as:

"Opop-C"
"Opoc-C"
"Orop-C"

or:

"Allivose-SP"
"Allrose-SP"
"Altrose-SP"

or:

"1 o.f."
"1 OD"
"1OT"
"1od"

The correct interpretation should be selected by considering BOTH:

A. what is visually written
B. what is medically/prescription-wise plausible

However, never invent a completely unrelated medicine.

============================================================
MEDICINE NAME RECOGNITION
============================================================

Medicine names are especially important.

When reading a medicine:

1. First inspect the entire handwritten word.
2. Identify individual character shapes.
3. Compare the beginning, middle, and ending of the word.
4. Consider common medicine-name patterns.
5. Consider the written dosage/strength.
6. Consider frequency.
7. Consider other medicines on the same prescription.
8. Use the surrounding clinical context.
9. Select the most plausible interpretation supported by the image.

Example:

If handwriting visually resembles:

"Opoc-C 200mg"

do not immediately assume the OCR result is exactly "Opoc-C".

Determine whether the handwriting more plausibly represents a known
medicine name based on:
- character shapes
- 200mg strength
- prescription context
- common medicine naming patterns

But NEVER replace it with an unrelated medicine simply because it is
medically common.

If no medically plausible interpretation is sufficiently supported,
return the closest visual transcription or "[UNCLEAR]".

============================================================
PRESCRIPTION ABBREVIATIONS
============================================================

Medical prescriptions commonly contain abbreviations.

Examples:

OD
BD
TDS
QID
HS
SOS
AC
PC
1-0-1
1-1-1
0-0-1

Do NOT automatically expand them.

If the handwriting visually resembles "OD" but OCR produces:

"o.f."
"1OT"
"1od"
"1 o.f."

inspect the actual character shapes and prescription context.

If it is clearly "OD", output:

"OD"

If it is genuinely uncertain, preserve the visually supported form
rather than inventing a different abbreviation.

Do NOT convert:

OD -> once daily

BD -> twice daily

TDS -> three times daily

unless the output schema explicitly requires expanded text.

============================================================
FREQUENCY / DOSAGE PATTERNS
============================================================

Prescription frequency often follows structured patterns.

Examples:

1-0-1
1-1-1
0-0-1
1-0-0

Interpret these patterns ONLY when the handwritten pattern is actually
visible.

Do not manufacture a frequency because a medicine normally uses one.

If frequency is unclear:

"frequency": "[UNCLEAR]"

If frequency is absent:

"frequency": ""

============================================================
DURATION
============================================================

Duration must be extracted only when visibly written.

Examples:

1 day
3 days
5 days
7 days
10 days

Do not calculate duration from quantity and frequency.

For example:

quantity = 10
frequency = 1-0-1

does NOT allow you to infer duration.

============================================================
DOSAGE
============================================================

Extract the medicine dosage/strength only when visibly associated
with that medicine.

Examples:

200mg
40mg
500 mg
0.05

Store the extracted dosage/strength in the "dosage" field.

Do not infer dosage from the medicine name.

Do not infer dosage from standard medical knowledge.

============================================================
INSTRUCTIONS
============================================================

Extract medicine-specific instructions only when visibly written.

Examples:

After food
Before food
With water
At bedtime
SOS

Store these instructions in the "instructions" field.

If no medicine-specific instruction is visible:

"instructions": ""

Do not invent instructions from medical knowledge.

============================================================
PATIENT INFORMATION
============================================================

Extract:

clinic
doctor
date
patient_name
age
sex

Use visual evidence plus reasonable recognition of handwriting.

Do not infer sex from the patient's name.

Do not infer age.

Do not change a date into another date.

============================================================
VITALS
============================================================

Extract:

bp
hr
spo2
temperature
weight

Common examples:

BP 120/70
HR 116/min
SPO2 98%
Temp 102.2 F

Preserve the actual visible value.

Do not confuse nearby handwritten notes with vitals.

For example, if:

Wt: ______

and below it the doctor writes:

"Dehydrated"

then:

weight = ""

notes = "Dehydrated"

Do NOT put "Dehydrated" into weight.

============================================================
COMPLAINTS / CLINICAL TEXT
============================================================

This section requires contextual medical recognition.

Doctors frequently write shorthand such as:

Cold
Cough
Fever
Throat infection
BAO x 1 day
URTI
etc.

If handwriting contains an abbreviated or poorly written complaint,
use medical context to understand the likely intended phrase.

However:

DO NOT invent a complaint that has no visual support.

If the writing appears to be:

"Cold, T. instert, Fever"

and the handwriting/context strongly indicates:

"Cold, T. infection, Fever"

then "T. infection" may be used because the interpretation is supported
by the visible shorthand and medical context.

But if multiple interpretations are equally plausible:

"[UNCLEAR]"

is preferred.

============================================================
IMPORTANT: DO NOT TURN COMPLAINTS INTO MEDICINES
============================================================

Text written after "Rx", below the patient information, or in the
clinical-history area is NOT automatically a medicine.

For example:

"BAO x 1 day"

must not become:

{
    "name": "BAO"
}

unless the prescription clearly places BAO in the medicine list.

Determine the role of text from:
- layout
- nearby labels
- handwriting position
- surrounding medicine entries

============================================================
MEDICINE LIST BOUNDARIES
============================================================

A medicine should normally appear as a separate item only when it is
actually part of the prescription's medicine list.

Do not accidentally convert:

complaints
diagnoses
clinical notes
duration
instructions

into medicine objects.

============================================================
VISUAL + CONTEXT REASONING
============================================================

Use the following hierarchy:

LEVEL 1:
What characters are visibly present?

LEVEL 2:
What word does the handwriting most closely resemble?

LEVEL 3:
Is that word consistent with a medical prescription?

LEVEL 4:
Does the dosage/strength support that interpretation?

LEVEL 5:
Does the frequency support that interpretation?

LEVEL 6:
Does the surrounding prescription context support it?

Only after these checks should you produce the final value.

============================================================
DO NOT OVER-CORRECT
============================================================

Medical knowledge is a supporting signal, NOT permission to hallucinate.

Bad:

Visual text:
"Opoc-C"

Model decides:
"Paracetamol"

This is NOT acceptable unless the handwriting itself provides strong
evidence for that interpretation.

Good:

Visual text resembles:
"Opoc-C"

Medical/prescription context suggests a specific plausible medicine.

If the visual evidence and context agree, use the recognized medicine.

If they disagree strongly, use "[UNCLEAR]".

============================================================
HANDWRITING CHARACTER CONFUSION
============================================================

Pay special attention to common handwriting/OCR confusions:

O / 0
I / l / 1
S / 5
B / 8
G / 6
C / O
D / 0
m / n
r / v
u / o
c / e
P / F
T / I

Do not mechanically replace characters.

Use the whole word and medical context.

============================================================
DOCTOR HANDWRITING STYLE
============================================================

Doctors often write:

- abbreviated medicine names
- incomplete-looking words
- merged characters
- shorthand
- non-standard spacing
- repeated frequency patterns
- medicine + dosage/strength on the same line
- frequency below the medicine name

Therefore, do NOT judge handwriting using normal English spelling rules.

A word that looks misspelled may actually be a medicine name.

============================================================
OUTPUT RULES
============================================================

Return ONLY valid JSON.

No:
- explanation
- markdown
- reasoning
- <think>
- code fences
- commentary


Use EXACTLY this structure:

{
  "patientId": null,
  "doctorId": null,
  "complaints": [],
  "diagnosis": [],
  "appointmentId": null,
  "sharedWithDoctors": [],
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
  "attachments": [],
  "followUpDate": null
}

DO NOT add fields outside this structure.

DO NOT return clinic, doctor, date, patient_name, age, sex, vitals,
or notes.

DO NOT return strength or quantity.

complaints, diagnosis, and tests MUST be arrays of strings.

Medicine objects MUST contain only:
name, dosage, frequency, duration, instructions.

If a value is not visibly present, return an empty string.
For followUpDate, return null when it is not visibly present.

DO NOT infer missing dosage, frequency, duration, or instructions.

============================================================
FINAL DECISION RULE
============================================================

For every uncertain handwritten value ask internally:

1. What do I visually see?
2. What are the possible readings?
3. Which reading best matches the handwriting?
4. Is that reading medically/prescription-wise plausible?
5. Does the surrounding prescription support it?
6. Am I inventing anything that is not supported?

Choose the most strongly supported interpretation.

If confidence is low:

"[UNCLEAR]"

is better than hallucinating.

The goal is NOT literal character-by-character OCR.

The goal is:

ACCURATE HUMAN-LIKE READING OF A HANDWRITTEN MEDICAL PRESCRIPTION
USING VISUAL EVIDENCE + MEDICAL PRESCRIPTION CONTEXT.
"""

# ============================================================
# IMAGE OCR
# ============================================================

async def extract_text_from_image(
    image_path: str,
) -> dict[str, Any]:

    base64_image = encode_image(image_path)

    response = await client.chat.completions.create(
        model=VISION_MODEL,

        reasoning_effort="none",

        response_format={
            "type": "json_object"
        },

        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": OCR_PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                "data:image/jpeg;base64,"
                                f"{base64_image}"
                            )
                        },
                    },
                ],
            }
        ],

        temperature=0,
        max_completion_tokens=1200
    )

    choice = response.choices[0]

    print("\n--- FINISH REASON ---")
    print(
        getattr(
            choice,
            "finish_reason",
            None
        )
    )

    raw_text = choice.message.content

    if not raw_text:
        raise ValueError(
            "Groq returned an empty OCR response."
        )

    return parse_json_response(raw_text)


# ============================================================
# BUILD FULL PRESCRIPTION DOCUMENT
# ============================================================
#
# OCR_PROMPT ONLY extracts fields that are actually visible on the
# handwritten prescription: complaints, diagnosis, medicines, tests,
# advice, followUpDate.
#
# patientId, doctorId, appointmentId, sharedWithDoctors and
# attachments are NOT extractable from handwriting -- they come from
# your application/session context (who is logged in, which
# appointment this belongs to, the uploaded file's own URL).
#
# This function merges the OCR result with that app-level context so
# the final dict matches the Mongoose `prescriptionSchema` exactly
# and can be passed straight into `Prescription.create(...)`.
# ============================================================

def build_prescription_document(
    ocr_result: dict[str, Any],
    patient_id: str,
    doctor_id: str,
    appointment_id: str,
    attachments: list[str] | None = None,
    shared_with_doctors: list[str] | None = None,
) -> dict[str, Any]:

    if not patient_id:
        raise ValueError("patient_id is required.")

    if not doctor_id:
        raise ValueError("doctor_id is required.")

    if not appointment_id:
        raise ValueError("appointment_id is required.")

    follow_up_date = ocr_result.get("followUpDate")

    return {
        "patientId": patient_id,
        "doctorId": doctor_id,
        "appointmentId": appointment_id,
        "sharedWithDoctors": shared_with_doctors or [],

        "complaints": ocr_result.get("complaints", []),
        "diagnosis": ocr_result.get("diagnosis", []),
        "medicines": ocr_result.get("medicines", []),
        "tests": ocr_result.get("tests", []),
        "advice": ocr_result.get("advice", ""),

        "attachments": attachments or [],

        "followUpDate": follow_up_date if follow_up_date else None,
    }

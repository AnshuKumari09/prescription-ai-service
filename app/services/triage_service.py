from app.rules.triage_rules import (
    EMERGENCY_SYMPTOM_RULES,
    SPECIALTY_MAPPING,
    URGENT_SYMPTOM_RULES,
)
from app.schemas.triage import (
    DecisionReason,
    RedFlag,
    TriageRequest,
    TriageResponse,
)


def normalize_text(value: str) -> str:
    return " ".join(
        value.strip().lower().split()
    )


def get_normalized_symptoms(
    request: TriageRequest,
) -> set[str]:

    return {
        normalize_text(symptom.name)
        for symptom in request.symptoms
    }


def determine_specialty(
    symptoms: set[str],
    pregnancy: bool,
) -> str:

    if pregnancy:
        return "gynecology"

    for symptom in symptoms:
        if symptom in SPECIALTY_MAPPING:
            return SPECIALTY_MAPPING[symptom]

    return "general_medicine"


def evaluate_symptom_rules(
    symptoms: set[str],
):
    red_flags = []
    reasons = []

    emergency_found = False
    urgent_found = False

    for rule in EMERGENCY_SYMPTOM_RULES:

        matched = symptoms.intersection(
            rule.symptoms
        )

        if matched:

            emergency_found = True

            for symptom in matched:
                red_flags.append(
                    RedFlag(
                        code=rule.code,
                        description=rule.description,
                        source="symptom",
                    )
                )

            reasons.append(
                DecisionReason(
                    code=rule.code,
                    description=rule.description,
                )
            )

    for rule in URGENT_SYMPTOM_RULES:

        matched = symptoms.intersection(
            rule.symptoms
        )

        if matched:

            urgent_found = True

            for symptom in matched:
                red_flags.append(
                    RedFlag(
                        code=rule.code,
                        description=rule.description,
                        source="symptom",
                    )
                )

            reasons.append(
                DecisionReason(
                    code=rule.code,
                    description=rule.description,
                )
            )

    return (
        emergency_found,
        urgent_found,
        red_flags,
        reasons,
    )


def evaluate_vitals(
    request: TriageRequest,
):

    red_flags = []
    reasons = []

    emergency = False
    urgent = False

    vitals = request.vitals

    if vitals is None:
        return (
            emergency,
            urgent,
            red_flags,
            reasons,
        )

    # Prototype threshold.
    # Must be clinically validated before production use.
    if vitals.spo2 is not None:

        if vitals.spo2 < 90:

            emergency = True

            red_flags.append(
                RedFlag(
                    code="LOW_SPO2",
                    description=(
                        "Oxygen saturation is below "
                        "the configured emergency threshold."
                    ),
                    source="vital",
                )
            )

            reasons.append(
                DecisionReason(
                    code="LOW_SPO2",
                    description=(
                        "Oxygen saturation requires "
                        "immediate clinical assessment."
                    ),
                )
            )

        elif vitals.spo2 < 94:

            urgent = True

            red_flags.append(
                RedFlag(
                    code="REDUCED_SPO2",
                    description=(
                        "Oxygen saturation is below "
                        "the configured urgent threshold."
                    ),
                    source="vital",
                )
            )

            reasons.append(
                DecisionReason(
                    code="REDUCED_SPO2",
                    description=(
                        "Oxygen saturation requires "
                        "prompt clinical assessment."
                    ),
                )
            )

    # Prototype threshold.
    if vitals.respiratory_rate is not None:

        if vitals.respiratory_rate > 30:

            urgent = True

            red_flags.append(
                RedFlag(
                    code="HIGH_RESPIRATORY_RATE",
                    description=(
                        "Respiratory rate is elevated."
                    ),
                    source="vital",
                )
            )

            reasons.append(
                DecisionReason(
                    code="HIGH_RESPIRATORY_RATE",
                    description=(
                        "Respiratory rate requires "
                        "prompt clinical assessment."
                    ),
                )
            )

    return (
        emergency,
        urgent,
        red_flags,
        reasons,
    )


def evaluate_special_conditions(
    request: TriageRequest,
):

    reasons = []
    red_flags = []

    # Pregnancy itself does not mean emergency.
    # It changes the clinical context.
    if request.pregnancy:

        reasons.append(
            DecisionReason(
                code="PREGNANCY",
                description=(
                    "Pregnancy is present and "
                    "requires pregnancy-aware clinical assessment."
                ),
            )
        )

    # Example of higher-risk context.
    high_risk_conditions = {
        normalize_text(condition)
        for condition
        in request.medical_history.chronic_conditions
    }

    if high_risk_conditions.intersection({
        "heart disease",
        "chronic kidney disease",
        "severe asthma",
    }):

        reasons.append(
            DecisionReason(
                code="HIGH_RISK_HISTORY",
                description=(
                    "Patient has a condition that "
                    "may require additional clinical consideration."
                ),
            )
        )

    return red_flags, reasons


def determine_missing_information(
    request: TriageRequest,
):

    missing = []

    if not request.symptoms:
        missing.append("symptoms")

    if request.vitals is None:
        missing.append("vitals")

    if request.chief_complaint is None:
        missing.append("chief_complaint")

    return missing


def triage_patient(
    request: TriageRequest,
) -> TriageResponse:

    symptoms = get_normalized_symptoms(
        request
    )

    (
        symptom_emergency,
        symptom_urgent,
        symptom_red_flags,
        symptom_reasons,
    ) = evaluate_symptom_rules(symptoms)

    (
        vital_emergency,
        vital_urgent,
        vital_red_flags,
        vital_reasons,
    ) = evaluate_vitals(request)

    (
        history_red_flags,
        history_reasons,
    ) = evaluate_special_conditions(request)

    red_flags = (
        symptom_red_flags
        + vital_red_flags
        + history_red_flags
    )

    reasons = (
        symptom_reasons
        + vital_reasons
        + history_reasons
    )

    emergency = (
        symptom_emergency
        or vital_emergency
    )

    urgent = (
        symptom_urgent
        or vital_urgent
    )

    specialty = determine_specialty(
        symptoms,
        request.pregnancy,
    )

    missing_information = (
        determine_missing_information(request)
    )

    if emergency:

        return TriageResponse(
            risk_level="EMERGENCY",
            priority="CRITICAL",
            red_flags=red_flags,
            decision_reasons=reasons,
            recommended_action=(
                "Immediate clinical assessment "
                "and emergency escalation should "
                "be considered according to the "
                "approved clinical protocol."
            ),
            suggested_specialty=specialty,
            requires_escalation=True,
            missing_information=missing_information,
        )

    if urgent:

        return TriageResponse(
            risk_level="URGENT",
            priority="HIGH",
            red_flags=red_flags,
            decision_reasons=reasons,
            recommended_action=(
                "Prioritize clinical assessment "
                "according to the approved "
                "triage protocol."
            ),
            suggested_specialty=specialty,
            requires_escalation=False,
            missing_information=missing_information,
        )

    return TriageResponse(
        risk_level="NORMAL",
        priority="ROUTINE",
        red_flags=red_flags,
        decision_reasons=reasons,
        recommended_action=(
            "Proceed with routine clinical "
            "consultation if appropriate."
        ),
        suggested_specialty=specialty,
        requires_escalation=False,
        missing_information=missing_information,
    )

from app.schemas.triage import (
    TriageAnalyzeRequest,
    TriageRequest,
    MedicalHistory,
    Symptom,
)


def analyze_patient(
    request: TriageAnalyzeRequest,
):
    from app.schemas.triage_extraction import (
        TriageExtractionRequest,
    )

    from app.services.triage_extraction_service import (
        extract_patient_information,
    )

    # -----------------------------------------
    # STEP 1: AI symptom extraction
    # -----------------------------------------

    extraction_request = TriageExtractionRequest(
        message=request.message,
        language=request.language,
    )

    extracted = extract_patient_information(
        extraction_request
    )

    # -----------------------------------------
    # STEP 2: Convert AI output into
    #          internal triage schema
    # -----------------------------------------

    symptoms = [
        Symptom(
            name=symptom.name,
            duration=symptom.duration,
            severity=symptom.severity,
            onset=symptom.onset,
            progression=symptom.progression,
        )
        for symptom in extracted.symptoms
    ]

    # -----------------------------------------
    # STEP 3: Build internal triage request
    # -----------------------------------------

    triage_request = TriageRequest(
        age=request.age,
        sex=request.sex,
        chief_complaint=(
            extracted.chief_complaint
            or request.message
        ),
        symptoms=symptoms,
        vitals=request.vitals,
        medical_history=request.medical_history,
        pregnancy=request.pregnancy,
    )

    # -----------------------------------------
    # STEP 4: Run deterministic triage engine
    # -----------------------------------------

    result = triage_patient(
        triage_request
    )

    return result
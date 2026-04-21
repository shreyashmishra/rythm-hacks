from datetime import date

from .models import Encounter, PatientProfile, User


def normalize_string_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [value for value in values if isinstance(value, str) and value.strip()]


def calculate_age(date_of_birth: date | None) -> int | None:
    if not date_of_birth:
        return None

    today = date.today()
    age = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    return age


def serialize_user(user: User) -> dict[str, str]:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
    }


def serialize_patient_profile(profile: PatientProfile) -> dict[str, object]:
    return {
        "id": profile.id,
        "fullName": profile.full_name,
        "dateOfBirth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
        "age": calculate_age(profile.date_of_birth),
        "sex": profile.sex,
        "allergies": normalize_string_list(profile.allergies),
        "chronicConditions": normalize_string_list(profile.chronic_conditions),
        "medications": normalize_string_list(profile.medications),
        "emergencyContactName": profile.emergency_contact_name,
        "emergencyContactPhone": profile.emergency_contact_phone,
    }


def _serialize_ai_version(
    *,
    summary: str | None,
    follow_up_window: str | None,
    clinical_considerations: list[str] | None,
    red_flags: list[str] | None,
    follow_up_questions: list[str] | None,
    follow_up_actions: list[str] | None,
    suggested_treatments: list[str] | None,
    urgency_score: int | None,
) -> dict[str, object] | None:
    if not any(
        [
            summary,
            follow_up_window,
            normalize_string_list(clinical_considerations),
            normalize_string_list(red_flags),
            normalize_string_list(follow_up_questions),
            normalize_string_list(follow_up_actions),
            normalize_string_list(suggested_treatments),
            urgency_score is not None,
        ]
    ):
        return None

    return {
        "preliminarySummary": summary,
        "recommendedFollowUpWindow": follow_up_window,
        "clinicalConsiderations": normalize_string_list(clinical_considerations),
        "redFlags": normalize_string_list(red_flags),
        "followUpQuestions": normalize_string_list(follow_up_questions),
        "followUpActions": normalize_string_list(follow_up_actions),
        "suggestedTreatments": normalize_string_list(suggested_treatments),
        "urgencyScore": urgency_score,
    }


def _build_ai_diff(
    generated: dict[str, object] | None,
    approved: dict[str, object] | None,
) -> dict[str, object]:
    if not generated or not approved:
        return {"changedFields": [], "changeCount": 0}

    changed_fields: list[str] = []
    for field_name, generated_value in generated.items():
        if approved.get(field_name) != generated_value:
            changed_fields.append(field_name)

    return {
        "changedFields": changed_fields,
        "changeCount": len(changed_fields),
    }


def serialize_encounter(
    encounter: Encounter,
    *,
    latest_job: dict[str, object] | None = None,
) -> dict[str, object]:
    generated = _serialize_ai_version(
        summary=encounter.ai_generated_summary or encounter.ai_preliminary_summary,
        follow_up_window=encounter.ai_generated_follow_up_window or encounter.ai_follow_up_window,
        clinical_considerations=(
            encounter.ai_generated_clinical_considerations or encounter.ai_clinical_considerations
        ),
        red_flags=encounter.ai_generated_red_flags or encounter.ai_red_flags,
        follow_up_questions=(
            encounter.ai_generated_follow_up_questions or encounter.ai_follow_up_questions
        ),
        follow_up_actions=encounter.ai_generated_follow_up_actions,
        suggested_treatments=(
            encounter.ai_generated_suggested_treatments or encounter.ai_suggested_treatments
        ),
        urgency_score=encounter.ai_generated_urgency_score,
    )
    approved = _serialize_ai_version(
        summary=encounter.ai_approved_summary,
        follow_up_window=encounter.ai_approved_follow_up_window,
        clinical_considerations=encounter.ai_approved_clinical_considerations,
        red_flags=encounter.ai_approved_red_flags,
        follow_up_questions=encounter.ai_approved_follow_up_questions,
        follow_up_actions=encounter.ai_approved_follow_up_actions,
        suggested_treatments=encounter.ai_approved_suggested_treatments,
        urgency_score=encounter.ai_approved_urgency_score,
    )
    current = approved or generated

    return {
        "id": encounter.id,
        "title": encounter.title,
        "summary": encounter.summary,
        "occurredAt": encounter.occurred_at.isoformat(),
        "doctorName": encounter.doctor_profile.full_name,
        "symptoms": [symptom.name for symptom in encounter.symptoms],
        "suggestedTreatments": [
            treatment.name for treatment in encounter.suggested_treatments
        ],
        "ai": {
            "status": encounter.ai_status.value,
            "disclaimer": encounter.ai_disclaimer,
            "generatedAt": (
                encounter.ai_generated_at.isoformat() if encounter.ai_generated_at else None
            ),
            "reviewedAt": (
                encounter.ai_reviewed_at.isoformat() if encounter.ai_reviewed_at else None
            ),
            "reviewedBy": (
                {
                    "id": encounter.reviewed_by_user.id,
                    "name": encounter.reviewed_by_user.name,
                    "role": encounter.reviewed_by_user.role.value,
                }
                if encounter.reviewed_by_user
                else None
            ),
            "generated": generated,
            "approved": approved,
            "current": current,
            "diff": _build_ai_diff(generated, approved),
            "reviewNotes": encounter.ai_review_notes,
            "job": latest_job,
        },
    }

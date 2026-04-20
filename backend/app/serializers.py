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


def serialize_encounter(encounter: Encounter) -> dict[str, object]:
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
            "status": encounter.ai_status or "not_requested",
            "disclaimer": encounter.ai_disclaimer,
            "preliminarySummary": encounter.ai_preliminary_summary,
            "recommendedFollowUpWindow": encounter.ai_follow_up_window,
            "clinicalConsiderations": normalize_string_list(
                encounter.ai_clinical_considerations
            ),
            "redFlags": normalize_string_list(encounter.ai_red_flags),
            "followUpQuestions": normalize_string_list(encounter.ai_follow_up_questions),
            "suggestedTreatments": normalize_string_list(
                encounter.ai_suggested_treatments
            ),
            "reviewNotes": encounter.ai_review_notes,
        },
    }

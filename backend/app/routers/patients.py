from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import AuthContext, require_role
from ..models import (
    DoctorProfile,
    Encounter,
    PatientProfile,
    Role,
    SuggestedTreatment,
    Symptom,
)
from ..schemas import (
    AiReviewUpdateRequest,
    EncounterCreateRequest,
    EncounterTreatmentUpdateRequest,
)
from ..services.ai import GeminiAiService
from ..serializers import calculate_age, serialize_encounter, serialize_patient_profile

router = APIRouter(prefix="/api", tags=["patients"])


def normalize_submitted_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        trimmed = value.strip()
        if trimmed and trimmed not in normalized:
            normalized.append(trimmed)
    return normalized


def get_doctor_profile(db: Session, user_id: str) -> DoctorProfile:
    doctor_profile = db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == user_id))
    if not doctor_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return doctor_profile


def get_patient_profile_by_user_id(db: Session, user_id: str) -> PatientProfile:
    patient_profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == user_id))
    if not patient_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return patient_profile


def get_patient_profile_by_id(db: Session, patient_profile_id: str) -> PatientProfile:
    patient_profile = db.scalar(
        select(PatientProfile).where(PatientProfile.id == patient_profile_id)
    )
    if not patient_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return patient_profile


def get_patient_encounters(db: Session, patient_profile_id: str) -> list[Encounter]:
    return list(
        db.scalars(
            select(Encounter)
            .where(Encounter.patient_profile_id == patient_profile_id)
            .options(
                selectinload(Encounter.doctor_profile),
                selectinload(Encounter.symptoms),
                selectinload(Encounter.suggested_treatments),
            )
            .order_by(Encounter.occurred_at.desc())
        )
    )


def get_encounter_with_relationships(db: Session, encounter_id: str) -> Encounter | None:
    return db.scalar(
        select(Encounter)
        .where(Encounter.id == encounter_id)
        .options(
            selectinload(Encounter.doctor_profile),
            selectinload(Encounter.symptoms),
            selectinload(Encounter.suggested_treatments),
        )
    )


@router.get("/patient/profile/me")
def patient_profile_me(
    auth: AuthContext = Depends(require_role(Role.patient)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_user_id(db, auth.user_id)
    return {"patient": serialize_patient_profile(patient_profile)}


@router.get("/patient/encounters/me")
def patient_encounters_me(
    auth: AuthContext = Depends(require_role(Role.patient)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_user_id(db, auth.user_id)
    encounters = get_patient_encounters(db, patient_profile.id)
    return {"encounters": [serialize_encounter(encounter) for encounter in encounters]}


@router.get("/doctor/patients")
def doctor_patients(
    _auth: AuthContext = Depends(require_role(Role.doctor)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patients = list(
        db.scalars(
            select(PatientProfile)
            .options(selectinload(PatientProfile.encounters))
            .order_by(PatientProfile.full_name.asc())
        )
    )

    return {
        "patients": [
            {
                "id": patient.id,
                "fullName": patient.full_name,
                "age": calculate_age(patient.date_of_birth),
                "sex": patient.sex,
                "lastEncounterAt": (
                    max(patient.encounters, key=lambda encounter: encounter.occurred_at).occurred_at.isoformat()
                    if patient.encounters
                    else None
                ),
            }
            for patient in patients
        ]
    }


@router.get("/doctor/patients/{patient_profile_id}")
def doctor_patient_profile(
    patient_profile_id: str,
    _auth: AuthContext = Depends(require_role(Role.doctor)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_id(db, patient_profile_id)
    return {"patient": serialize_patient_profile(patient_profile)}


@router.get("/doctor/patients/{patient_profile_id}/encounters")
def doctor_patient_encounters(
    patient_profile_id: str,
    _auth: AuthContext = Depends(require_role(Role.doctor)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_id(db, patient_profile_id)
    encounters = get_patient_encounters(db, patient_profile.id)
    return {"encounters": [serialize_encounter(encounter) for encounter in encounters]}


@router.post("/doctor/patients/{patient_profile_id}/encounters", status_code=status.HTTP_201_CREATED)
def create_doctor_encounter(
    patient_profile_id: str,
    payload: EncounterCreateRequest,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = get_doctor_profile(db, auth.user_id)
    patient_profile = get_patient_profile_by_id(db, patient_profile_id)

    symptoms = normalize_submitted_list(payload.symptoms)
    if not symptoms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one symptom is required",
        )

    suggested_treatments = normalize_submitted_list(payload.suggested_treatments)
    occurred_at = payload.occurred_at or datetime.utcnow()

    encounter = Encounter(
        patient_profile_id=patient_profile.id,
        doctor_profile_id=doctor_profile.id,
        title=payload.title,
        summary=payload.summary or None,
        occurred_at=occurred_at,
        symptoms=[Symptom(name=name) for name in symptoms],
        suggested_treatments=[
            SuggestedTreatment(name=name) for name in suggested_treatments
        ],
    )

    db.add(encounter)
    db.commit()
    encounter = get_encounter_with_relationships(db, encounter.id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Encounter save failed")

    return {"encounter": serialize_encounter(encounter)}


@router.patch("/doctor/encounters/{encounter_id}/treatments")
def update_encounter_treatments(
    encounter_id: str,
    payload: EncounterTreatmentUpdateRequest,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = get_doctor_profile(db, auth.user_id)
    encounter = db.scalar(
        select(Encounter).where(Encounter.id == encounter_id)
    )

    if not encounter or encounter.doctor_profile_id != doctor_profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    encounter.suggested_treatments.clear()
    for treatment_name in normalize_submitted_list(payload.suggested_treatments):
        encounter.suggested_treatments.append(SuggestedTreatment(name=treatment_name))

    db.commit()
    encounter = get_encounter_with_relationships(db, encounter_id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Encounter update failed")

    return {"encounter": serialize_encounter(encounter)}


@router.post("/doctor/encounters/{encounter_id}/ai-generate")
def generate_ai_for_encounter(
    encounter_id: str,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = get_doctor_profile(db, auth.user_id)
    encounter = get_encounter_with_relationships(db, encounter_id)

    if not encounter or encounter.doctor_profile_id != doctor_profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    patient_profile = get_patient_profile_by_id(db, encounter.patient_profile_id)

    try:
        ai_result = GeminiAiService().generate_preliminary_suggestions(patient_profile, encounter)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini request failed",
        ) from error

    encounter.ai_status = "generated"
    encounter.ai_disclaimer = ai_result.disclaimer
    encounter.ai_preliminary_summary = ai_result.preliminary_summary
    encounter.ai_follow_up_window = ai_result.recommended_follow_up_window
    encounter.ai_clinical_considerations = normalize_submitted_list(
        ai_result.clinical_considerations
    )
    encounter.ai_red_flags = normalize_submitted_list(ai_result.red_flags)
    encounter.ai_follow_up_questions = normalize_submitted_list(ai_result.follow_up_questions)
    encounter.ai_suggested_treatments = normalize_submitted_list(
        ai_result.suggested_treatments
    )
    db.commit()

    refreshed_encounter = get_encounter_with_relationships(db, encounter_id)
    if not refreshed_encounter:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI save failed")

    return {"encounter": serialize_encounter(refreshed_encounter)}


@router.patch("/doctor/encounters/{encounter_id}/ai-review")
def review_ai_for_encounter(
    encounter_id: str,
    payload: AiReviewUpdateRequest,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = get_doctor_profile(db, auth.user_id)
    encounter = db.scalar(select(Encounter).where(Encounter.id == encounter_id))

    if not encounter or encounter.doctor_profile_id != doctor_profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    encounter.ai_status = "reviewed"
    encounter.ai_preliminary_summary = payload.preliminary_summary
    encounter.ai_follow_up_window = payload.recommended_follow_up_window
    encounter.ai_clinical_considerations = normalize_submitted_list(
        payload.clinical_considerations
    )
    encounter.ai_red_flags = normalize_submitted_list(payload.red_flags)
    encounter.ai_follow_up_questions = normalize_submitted_list(payload.follow_up_questions)
    encounter.ai_suggested_treatments = normalize_submitted_list(payload.suggested_treatments)
    encounter.ai_review_notes = payload.review_notes or None

    encounter.suggested_treatments.clear()
    for treatment_name in encounter.ai_suggested_treatments:
        encounter.suggested_treatments.append(SuggestedTreatment(name=treatment_name))

    db.commit()
    refreshed_encounter = get_encounter_with_relationships(db, encounter_id)
    if not refreshed_encounter:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI review save failed")

    return {"encounter": serialize_encounter(refreshed_encounter)}

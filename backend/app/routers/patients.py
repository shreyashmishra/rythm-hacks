from collections.abc import Iterable
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, load_only, selectinload

from ..database import get_db
from ..dependencies import AuthContext, require_permission, require_role
from ..models import (
    DoctorProfile,
    Encounter,
    EncounterAiStatus,
    PatientProfile,
    Role,
    SuggestedTreatment,
    Symptom,
    User,
)
from ..schemas import AiReviewUpdateRequest, EncounterCreateRequest, EncounterTreatmentUpdateRequest
from ..serializers import calculate_age, serialize_encounter, serialize_patient_profile
from ..services.ai_jobs import (
    get_latest_ai_job,
    get_latest_ai_jobs_for_encounters,
    queue_ai_job,
    serialize_ai_job,
)
from ..services.audit import fetch_recent_audit_events, log_audit_event
from ..services.ehr_cache import (
    cache_patient_encounters,
    get_cached_patient_encounters,
    invalidate_patient_encounters,
)

router = APIRouter(prefix="/api", tags=["patients"])


ENCOUNTER_READ_OPTIONS = (
    load_only(
        Encounter.id,
        Encounter.title,
        Encounter.summary,
        Encounter.occurred_at,
        Encounter.doctor_profile_id,
        Encounter.ai_status,
        Encounter.ai_disclaimer,
        Encounter.ai_preliminary_summary,
        Encounter.ai_follow_up_window,
        Encounter.ai_clinical_considerations,
        Encounter.ai_red_flags,
        Encounter.ai_follow_up_questions,
        Encounter.ai_suggested_treatments,
        Encounter.ai_review_notes,
        Encounter.ai_generated_at,
        Encounter.ai_generated_summary,
        Encounter.ai_generated_follow_up_window,
        Encounter.ai_generated_clinical_considerations,
        Encounter.ai_generated_red_flags,
        Encounter.ai_generated_follow_up_questions,
        Encounter.ai_generated_follow_up_actions,
        Encounter.ai_generated_suggested_treatments,
        Encounter.ai_generated_urgency_score,
        Encounter.ai_reviewed_at,
        Encounter.ai_reviewed_by_user_id,
        Encounter.ai_approved_summary,
        Encounter.ai_approved_follow_up_window,
        Encounter.ai_approved_clinical_considerations,
        Encounter.ai_approved_red_flags,
        Encounter.ai_approved_follow_up_questions,
        Encounter.ai_approved_follow_up_actions,
        Encounter.ai_approved_suggested_treatments,
        Encounter.ai_approved_urgency_score,
    ),
    joinedload(Encounter.doctor_profile).load_only(
        DoctorProfile.id,
        DoctorProfile.full_name,
    ),
    joinedload(Encounter.reviewed_by_user).load_only(
        User.id,
        User.name,
        User.role,
    ),
    selectinload(Encounter.symptoms).load_only(
        Symptom.id,
        Symptom.name,
    ),
    selectinload(Encounter.suggested_treatments).load_only(
        SuggestedTreatment.id,
        SuggestedTreatment.name,
    ),
)


def normalize_submitted_list(values: Iterable[str]) -> list[str]:
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


def get_serialized_patient_encounters(
    db: Session, patient_profile_id: str
) -> list[dict[str, object]]:
    cached_encounters = get_cached_patient_encounters(patient_profile_id)
    if cached_encounters is not None:
        return cached_encounters

    encounters = db.scalars(
        select(Encounter)
        .where(Encounter.patient_profile_id == patient_profile_id)
        .options(*ENCOUNTER_READ_OPTIONS)
        .order_by(Encounter.occurred_at.desc())
    ).all()

    latest_jobs_by_encounter = get_latest_ai_jobs_for_encounters(
        db, [encounter.id for encounter in encounters]
    )
    serialized_encounters = [
        serialize_encounter(encounter, latest_job=latest_jobs_by_encounter.get(encounter.id))
        for encounter in encounters
    ]
    cache_patient_encounters(patient_profile_id, serialized_encounters)
    return serialized_encounters


def get_encounter_with_relationships(db: Session, encounter_id: str) -> Encounter | None:
    return db.scalar(
        select(Encounter)
        .where(Encounter.id == encounter_id)
        .options(*ENCOUNTER_READ_OPTIONS)
    )


@router.get("/patient/profile/me")
def patient_profile_me(
    auth: AuthContext = Depends(require_role(Role.patient)),
    _permission: AuthContext = Depends(require_permission("patient:read:self")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_user_id(db, auth.user_id)
    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="patient.profile_viewed_self",
        resource_type="patient_profile",
        resource_id=patient_profile.id,
        patient_profile_id=patient_profile.id,
        details={"scope": "self"},
    )
    db.commit()
    return {"patient": serialize_patient_profile(patient_profile)}


@router.get("/patient/encounters/me")
def patient_encounters_me(
    auth: AuthContext = Depends(require_role(Role.patient)),
    _permission: AuthContext = Depends(require_permission("patient:read:self")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_user_id(db, auth.user_id)
    encounters = get_serialized_patient_encounters(db, patient_profile.id)
    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="patient.encounters_viewed_self",
        resource_type="patient_profile",
        resource_id=patient_profile.id,
        patient_profile_id=patient_profile.id,
        details={"encounterCount": len(encounters)},
    )
    db.commit()
    return {"encounters": encounters}


@router.get("/patient/activity/me")
def patient_activity_me(
    auth: AuthContext = Depends(require_role(Role.patient)),
    _permission: AuthContext = Depends(require_permission("patient:read:audit:self")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_user_id(db, auth.user_id)
    activity = fetch_recent_audit_events(db, patient_profile_id=patient_profile.id)
    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="patient.audit_viewed_self",
        resource_type="patient_profile",
        resource_id=patient_profile.id,
        patient_profile_id=patient_profile.id,
        details={"eventCount": len(activity)},
    )
    db.commit()
    return {"activity": activity}


@router.get("/doctor/patients")
def doctor_patients(
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:read:patients")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    latest_encounter_subquery = (
        select(
            Encounter.patient_profile_id.label("patient_profile_id"),
            func.max(Encounter.occurred_at).label("last_encounter_at"),
        )
        .group_by(Encounter.patient_profile_id)
        .subquery()
    )

    patients = db.execute(
        select(
            PatientProfile.id,
            PatientProfile.full_name,
            PatientProfile.date_of_birth,
            PatientProfile.sex,
            latest_encounter_subquery.c.last_encounter_at,
        )
        .outerjoin(
            latest_encounter_subquery,
            latest_encounter_subquery.c.patient_profile_id == PatientProfile.id,
        )
        .order_by(PatientProfile.full_name.asc())
    ).all()

    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="doctor.patient_directory_viewed",
        resource_type="patient_directory",
        resource_id=None,
        details={"patientCount": len(patients)},
    )
    db.commit()

    return {
        "patients": [
            {
                "id": patient.id,
                "fullName": patient.full_name,
                "age": calculate_age(patient.date_of_birth),
                "sex": patient.sex,
                "lastEncounterAt": (
                    patient.last_encounter_at.isoformat()
                    if patient.last_encounter_at
                    else None
                ),
            }
            for patient in patients
        ]
    }


@router.get("/doctor/patients/{patient_profile_id}")
def doctor_patient_profile(
    patient_profile_id: str,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:read:patients")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_id(db, patient_profile_id)
    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="doctor.patient_profile_viewed",
        resource_type="patient_profile",
        resource_id=patient_profile.id,
        patient_profile_id=patient_profile.id,
        details={"scope": "doctor"},
    )
    db.commit()
    return {"patient": serialize_patient_profile(patient_profile)}


@router.get("/doctor/patients/{patient_profile_id}/encounters")
def doctor_patient_encounters(
    patient_profile_id: str,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:read:patients")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_id(db, patient_profile_id)
    encounters = get_serialized_patient_encounters(db, patient_profile.id)
    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="doctor.patient_encounters_viewed",
        resource_type="patient_profile",
        resource_id=patient_profile.id,
        patient_profile_id=patient_profile.id,
        details={"encounterCount": len(encounters)},
    )
    db.commit()
    return {"encounters": encounters}


@router.get("/doctor/patients/{patient_profile_id}/activity")
def doctor_patient_activity(
    patient_profile_id: str,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:read:audit")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = get_patient_profile_by_id(db, patient_profile_id)
    activity = fetch_recent_audit_events(db, patient_profile_id=patient_profile.id)
    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="doctor.patient_audit_viewed",
        resource_type="patient_profile",
        resource_id=patient_profile.id,
        patient_profile_id=patient_profile.id,
        details={"eventCount": len(activity)},
    )
    db.commit()
    return {"activity": activity}


@router.post("/doctor/patients/{patient_profile_id}/encounters", status_code=status.HTTP_201_CREATED)
def create_doctor_encounter(
    patient_profile_id: str,
    payload: EncounterCreateRequest,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:write:encounters")),
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
    db.flush()
    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="doctor.encounter_created",
        resource_type="encounter",
        resource_id=encounter.id,
        patient_profile_id=patient_profile.id,
        encounter_id=encounter.id,
        details={"symptomCount": len(symptoms)},
    )
    db.commit()
    invalidate_patient_encounters(patient_profile.id)
    encounter = get_encounter_with_relationships(db, encounter.id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Encounter save failed")

    latest_jobs = get_latest_ai_jobs_for_encounters(db, [encounter.id])
    return {"encounter": serialize_encounter(encounter, latest_job=latest_jobs.get(encounter.id))}


@router.patch("/doctor/encounters/{encounter_id}/treatments")
def update_encounter_treatments(
    encounter_id: str,
    payload: EncounterTreatmentUpdateRequest,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:write:encounters")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = get_doctor_profile(db, auth.user_id)
    encounter = db.scalar(select(Encounter).where(Encounter.id == encounter_id))

    if not encounter or encounter.doctor_profile_id != doctor_profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    encounter.suggested_treatments.clear()
    normalized_treatments = normalize_submitted_list(payload.suggested_treatments)
    for treatment_name in normalized_treatments:
        encounter.suggested_treatments.append(SuggestedTreatment(name=treatment_name))

    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="doctor.encounter_treatments_updated",
        resource_type="encounter",
        resource_id=encounter.id,
        patient_profile_id=encounter.patient_profile_id,
        encounter_id=encounter.id,
        details={"treatmentCount": len(normalized_treatments)},
    )
    db.commit()
    invalidate_patient_encounters(encounter.patient_profile_id)
    encounter = get_encounter_with_relationships(db, encounter_id)
    if not encounter:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Encounter update failed")

    latest_jobs = get_latest_ai_jobs_for_encounters(db, [encounter.id])
    return {"encounter": serialize_encounter(encounter, latest_job=latest_jobs.get(encounter.id))}


@router.post("/doctor/encounters/{encounter_id}/ai-generate", status_code=status.HTTP_202_ACCEPTED)
def generate_ai_for_encounter(
    encounter_id: str,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:review:ai")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = get_doctor_profile(db, auth.user_id)
    encounter = db.scalar(select(Encounter).where(Encounter.id == encounter_id))

    if not encounter or encounter.doctor_profile_id != doctor_profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    job, created = queue_ai_job(
        db,
        encounter=encounter,
        requested_by_user_id=auth.user_id,
    )
    return {
        "job": serialize_ai_job(job),
        "reusedExistingJob": not created,
    }


@router.get("/doctor/encounters/{encounter_id}/ai-job")
def latest_ai_job_for_encounter(
    encounter_id: str,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:review:ai")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = get_doctor_profile(db, auth.user_id)
    encounter = db.scalar(select(Encounter).where(Encounter.id == encounter_id))

    if not encounter or encounter.doctor_profile_id != doctor_profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    return {"job": serialize_ai_job(get_latest_ai_job(db, encounter_id))}


@router.patch("/doctor/encounters/{encounter_id}/ai-review")
def review_ai_for_encounter(
    encounter_id: str,
    payload: AiReviewUpdateRequest,
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:review:ai")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = get_doctor_profile(db, auth.user_id)
    encounter = db.scalar(select(Encounter).where(Encounter.id == encounter_id))

    if not encounter or encounter.doctor_profile_id != doctor_profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    if not (encounter.ai_generated_summary or encounter.ai_preliminary_summary):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Generate AI output before reviewing it",
        )

    encounter.ai_status = EncounterAiStatus.reviewed
    encounter.ai_review_notes = payload.review_notes or None
    encounter.ai_reviewed_at = datetime.utcnow()
    encounter.ai_reviewed_by_user_id = auth.user_id
    encounter.ai_approved_summary = payload.preliminary_summary
    encounter.ai_approved_follow_up_window = payload.recommended_follow_up_window
    encounter.ai_approved_clinical_considerations = normalize_submitted_list(
        payload.clinical_considerations
    )
    encounter.ai_approved_red_flags = normalize_submitted_list(payload.red_flags)
    encounter.ai_approved_follow_up_questions = normalize_submitted_list(payload.follow_up_questions)
    encounter.ai_approved_follow_up_actions = normalize_submitted_list(payload.follow_up_actions)
    encounter.ai_approved_suggested_treatments = normalize_submitted_list(
        payload.suggested_treatments
    )
    encounter.ai_approved_urgency_score = payload.urgency_score

    encounter.ai_preliminary_summary = encounter.ai_approved_summary
    encounter.ai_follow_up_window = encounter.ai_approved_follow_up_window
    encounter.ai_clinical_considerations = encounter.ai_approved_clinical_considerations
    encounter.ai_red_flags = encounter.ai_approved_red_flags
    encounter.ai_follow_up_questions = encounter.ai_approved_follow_up_questions
    encounter.ai_suggested_treatments = encounter.ai_approved_suggested_treatments

    encounter.suggested_treatments.clear()
    for treatment_name in encounter.ai_approved_suggested_treatments:
        encounter.suggested_treatments.append(SuggestedTreatment(name=treatment_name))

    log_audit_event(
        db,
        actor_user_id=auth.user_id,
        action="doctor.encounter_ai_reviewed",
        resource_type="encounter",
        resource_id=encounter.id,
        patient_profile_id=encounter.patient_profile_id,
        encounter_id=encounter.id,
        details={
            "changedFields": [
                field_name
                for field_name, generated_value, approved_value in [
                    ("preliminarySummary", encounter.ai_generated_summary, encounter.ai_approved_summary),
                    (
                        "recommendedFollowUpWindow",
                        encounter.ai_generated_follow_up_window,
                        encounter.ai_approved_follow_up_window,
                    ),
                    (
                        "clinicalConsiderations",
                        encounter.ai_generated_clinical_considerations,
                        encounter.ai_approved_clinical_considerations,
                    ),
                    ("redFlags", encounter.ai_generated_red_flags, encounter.ai_approved_red_flags),
                    (
                        "followUpQuestions",
                        encounter.ai_generated_follow_up_questions,
                        encounter.ai_approved_follow_up_questions,
                    ),
                    (
                        "followUpActions",
                        encounter.ai_generated_follow_up_actions,
                        encounter.ai_approved_follow_up_actions,
                    ),
                    (
                        "suggestedTreatments",
                        encounter.ai_generated_suggested_treatments,
                        encounter.ai_approved_suggested_treatments,
                    ),
                    ("urgencyScore", encounter.ai_generated_urgency_score, encounter.ai_approved_urgency_score),
                ]
                if generated_value != approved_value
            ],
        },
    )

    db.commit()
    invalidate_patient_encounters(encounter.patient_profile_id)
    refreshed_encounter = get_encounter_with_relationships(db, encounter_id)
    if not refreshed_encounter:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI review save failed")

    latest_jobs = get_latest_ai_jobs_for_encounters(db, [refreshed_encounter.id])
    return {
        "encounter": serialize_encounter(
            refreshed_encounter,
            latest_job=latest_jobs.get(refreshed_encounter.id),
        )
    }

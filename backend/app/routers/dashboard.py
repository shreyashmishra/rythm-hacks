from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import AuthContext, require_permission, require_role
from ..models import DoctorProfile, Encounter, EncounterAiStatus, PatientProfile, Role

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/patient/dashboard")
def patient_dashboard(
    auth: AuthContext = Depends(require_role(Role.patient)),
    _permission: AuthContext = Depends(require_permission("patient:read:self")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == auth.user_id))
    encounter_count = 0
    reviewed_encounter_count = 0
    if patient_profile:
        encounter_count = db.scalar(
            select(func.count(Encounter.id)).where(
                Encounter.patient_profile_id == patient_profile.id
            )
        ) or 0
        reviewed_encounter_count = db.scalar(
            select(func.count(Encounter.id)).where(
                Encounter.patient_profile_id == patient_profile.id,
                Encounter.ai_status == EncounterAiStatus.reviewed,
            )
        ) or 0

    return {
        "title": "Patient dashboard",
        "subtitle": "Review your profile, encounter history, and access activity in one place.",
        "encounterCount": encounter_count,
        "reviewedEncounterCount": reviewed_encounter_count,
    }


@router.get("/doctor/dashboard")
def doctor_dashboard(
    auth: AuthContext = Depends(require_role(Role.doctor)),
    _permission: AuthContext = Depends(require_permission("doctor:read:patients")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == auth.user_id))
    encounter_count = 0
    pending_ai_review_count = 0
    high_risk_count = 0
    if doctor_profile:
        encounter_count = db.scalar(
            select(func.count(Encounter.id)).where(
                Encounter.doctor_profile_id == doctor_profile.id
            )
        ) or 0
        pending_ai_review_count = db.scalar(
            select(func.count(Encounter.id)).where(
                Encounter.doctor_profile_id == doctor_profile.id,
                Encounter.ai_status.in_(
                    [
                        EncounterAiStatus.queued,
                        EncounterAiStatus.processing,
                        EncounterAiStatus.generated,
                    ]
                ),
            )
        ) or 0
        high_risk_count = db.scalar(
            select(func.count(Encounter.id)).where(
                Encounter.doctor_profile_id == doctor_profile.id,
                or_(
                    Encounter.ai_approved_urgency_score >= 4,
                    Encounter.ai_generated_urgency_score >= 4,
                ),
            )
        ) or 0

    patient_count = db.scalar(select(func.count(PatientProfile.id))) or 0

    return {
        "title": "Doctor dashboard",
        "subtitle": "Browse patients, monitor pending AI review, and track higher-risk encounters.",
        "encounterCount": encounter_count,
        "patientCount": patient_count,
        "pendingAiReviewCount": pending_ai_review_count,
        "highRiskCount": high_risk_count,
    }

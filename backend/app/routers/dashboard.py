from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import AuthContext, require_role
from ..models import DoctorProfile, Encounter, PatientProfile, Role

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/patient/dashboard")
def patient_dashboard(
    auth: AuthContext = Depends(require_role(Role.patient)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    patient_profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == auth.user_id))
    encounter_count = 0
    if patient_profile:
        encounter_count = db.scalar(
            select(func.count(Encounter.id)).where(
                Encounter.patient_profile_id == patient_profile.id
            )
        ) or 0

    return {
        "title": "Patient dashboard",
        "subtitle": "Review your profile and encounter history in one place.",
        "encounterCount": encounter_count,
    }


@router.get("/doctor/dashboard")
def doctor_dashboard(
    auth: AuthContext = Depends(require_role(Role.doctor)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    doctor_profile = db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == auth.user_id))
    encounter_count = 0
    if doctor_profile:
        encounter_count = db.scalar(
            select(func.count(Encounter.id)).where(
                Encounter.doctor_profile_id == doctor_profile.id
            )
        ) or 0

    patient_count = db.scalar(select(func.count(PatientProfile.id))) or 0

    return {
        "title": "Doctor dashboard",
        "subtitle": "Browse patient profiles and review encounter history.",
        "encounterCount": encounter_count,
        "patientCount": patient_count,
    }

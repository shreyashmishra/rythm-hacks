from __future__ import annotations

from datetime import UTC, datetime
from threading import Thread

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import SessionLocal
from ..models import AiJob, AiJobStatus, Encounter, EncounterAiStatus, PatientProfile, Symptom
from ..schemas import AiSuggestionResponse
from .ai import GeminiAiService
from .audit import log_audit_event
from .ehr_cache import invalidate_patient_encounters


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _normalize_list(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        trimmed = value.strip()
        if trimmed and trimmed not in normalized:
            normalized.append(trimmed)
    return normalized


def serialize_ai_job(job: AiJob | None) -> dict[str, object] | None:
    if not job:
        return None

    return {
        "id": job.id,
        "status": job.status.value,
        "errorMessage": job.error_message,
        "createdAt": job.created_at.isoformat(),
        "startedAt": job.started_at.isoformat() if job.started_at else None,
        "completedAt": job.completed_at.isoformat() if job.completed_at else None,
    }


def get_latest_ai_jobs_for_encounters(
    db: Session,
    encounter_ids: list[str],
) -> dict[str, dict[str, object] | None]:
    if not encounter_ids:
        return {}

    jobs = db.scalars(
        select(AiJob)
        .where(AiJob.encounter_id.in_(encounter_ids))
        .order_by(AiJob.created_at.desc())
    ).all()

    latest_jobs: dict[str, dict[str, object] | None] = {}
    for job in jobs:
        if job.encounter_id in latest_jobs:
            continue
        latest_jobs[job.encounter_id] = serialize_ai_job(job)

    for encounter_id in encounter_ids:
        latest_jobs.setdefault(encounter_id, None)

    return latest_jobs


def get_active_ai_job(db: Session, encounter_id: str) -> AiJob | None:
    return db.scalar(
        select(AiJob)
        .where(
            AiJob.encounter_id == encounter_id,
            AiJob.status.in_([AiJobStatus.queued, AiJobStatus.processing]),
        )
        .order_by(AiJob.created_at.desc())
    )


def get_latest_ai_job(db: Session, encounter_id: str) -> AiJob | None:
    return db.scalar(
        select(AiJob)
        .where(AiJob.encounter_id == encounter_id)
        .order_by(AiJob.created_at.desc())
    )


def queue_ai_job(
    db: Session,
    *,
    encounter: Encounter,
    requested_by_user_id: str,
) -> tuple[AiJob, bool]:
    active_job = get_active_ai_job(db, encounter.id)
    if active_job:
        return active_job, False

    encounter.ai_status = EncounterAiStatus.queued
    job = AiJob(
        encounter_id=encounter.id,
        patient_profile_id=encounter.patient_profile_id,
        requested_by_user_id=requested_by_user_id,
        status=AiJobStatus.queued,
    )
    db.add(job)
    db.flush()
    log_audit_event(
        db,
        actor_user_id=requested_by_user_id,
        action="encounter.ai_generation_queued",
        resource_type="encounter",
        resource_id=encounter.id,
        patient_profile_id=encounter.patient_profile_id,
        encounter_id=encounter.id,
        details={"jobId": job.id},
    )
    db.commit()
    db.refresh(job)
    invalidate_patient_encounters(encounter.patient_profile_id)

    Thread(target=_process_ai_job, args=(job.id,), daemon=True).start()
    return job, True


def _load_encounter_for_job(db: Session, encounter_id: str) -> Encounter | None:
    return db.scalar(
        select(Encounter)
        .where(Encounter.id == encounter_id)
        .options(selectinload(Encounter.symptoms).load_only(Symptom.name))
    )


def _apply_generated_output(encounter: Encounter, ai_result: AiSuggestionResponse) -> None:
    encounter.ai_status = EncounterAiStatus.generated
    encounter.ai_disclaimer = ai_result.disclaimer
    encounter.ai_generated_at = _utcnow()
    encounter.ai_generated_summary = ai_result.preliminary_summary
    encounter.ai_generated_follow_up_window = ai_result.recommended_follow_up_window
    encounter.ai_generated_clinical_considerations = _normalize_list(
        ai_result.clinical_considerations
    )
    encounter.ai_generated_red_flags = _normalize_list(
        list(ai_result.red_flags) + list(ai_result.possible_risks)
    )
    encounter.ai_generated_follow_up_questions = _normalize_list(
        ai_result.follow_up_questions
    )
    encounter.ai_generated_follow_up_actions = _normalize_list(
        ai_result.follow_up_actions
    )
    encounter.ai_generated_suggested_treatments = _normalize_list(
        ai_result.suggested_treatments
    )
    encounter.ai_generated_urgency_score = ai_result.urgency_score

    # Preserve legacy columns so existing clients and data stay coherent.
    encounter.ai_preliminary_summary = encounter.ai_generated_summary
    encounter.ai_follow_up_window = encounter.ai_generated_follow_up_window
    encounter.ai_clinical_considerations = encounter.ai_generated_clinical_considerations
    encounter.ai_red_flags = encounter.ai_generated_red_flags
    encounter.ai_follow_up_questions = encounter.ai_generated_follow_up_questions
    encounter.ai_suggested_treatments = encounter.ai_generated_suggested_treatments

    # Regeneration invalidates the prior approval so the doctor explicitly re-approves.
    encounter.ai_review_notes = None
    encounter.ai_reviewed_at = None
    encounter.ai_reviewed_by_user_id = None
    encounter.ai_approved_summary = None
    encounter.ai_approved_follow_up_window = None
    encounter.ai_approved_clinical_considerations = None
    encounter.ai_approved_red_flags = None
    encounter.ai_approved_follow_up_questions = None
    encounter.ai_approved_follow_up_actions = None
    encounter.ai_approved_suggested_treatments = None
    encounter.ai_approved_urgency_score = None


def _process_ai_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(AiJob, job_id)
        if not job:
            return

        encounter = _load_encounter_for_job(db, job.encounter_id)
        patient_profile = db.get(PatientProfile, job.patient_profile_id)
        if not encounter or not patient_profile:
            job.status = AiJobStatus.failed
            job.error_message = "Encounter or patient profile was not found"
            job.completed_at = _utcnow()
            if encounter:
                encounter.ai_status = EncounterAiStatus.failed
            db.commit()
            return

        job.status = AiJobStatus.processing
        job.started_at = _utcnow()
        encounter.ai_status = EncounterAiStatus.processing
        db.commit()
        invalidate_patient_encounters(encounter.patient_profile_id)

        ai_result = GeminiAiService().generate_preliminary_suggestions(
            patient_profile, encounter
        )

        encounter = _load_encounter_for_job(db, job.encounter_id)
        if not encounter:
            job.status = AiJobStatus.failed
            job.error_message = "Encounter was not found after generation"
            job.completed_at = _utcnow()
            db.commit()
            return

        _apply_generated_output(encounter, ai_result)
        job.status = AiJobStatus.completed
        job.error_message = None
        job.completed_at = _utcnow()
        log_audit_event(
            db,
            actor_user_id=job.requested_by_user_id,
            action="encounter.ai_generation_completed",
            resource_type="encounter",
            resource_id=encounter.id,
            patient_profile_id=encounter.patient_profile_id,
            encounter_id=encounter.id,
            details={
                "jobId": job.id,
                "urgencyScore": ai_result.urgency_score,
                "redFlagCount": len(encounter.ai_generated_red_flags or []),
            },
        )
        db.commit()
        invalidate_patient_encounters(encounter.patient_profile_id)
    except RuntimeError as error:
        _mark_job_failed(db, job_id, str(error))
    except Exception:
        _mark_job_failed(db, job_id, "Gemini request failed")
    finally:
        db.close()


def _mark_job_failed(db: Session, job_id: str, error_message: str) -> None:
    job = db.get(AiJob, job_id)
    if not job:
        return

    encounter = db.get(Encounter, job.encounter_id)
    job.status = AiJobStatus.failed
    job.error_message = error_message
    job.completed_at = _utcnow()
    if encounter:
        encounter.ai_status = EncounterAiStatus.failed
        log_audit_event(
            db,
            actor_user_id=job.requested_by_user_id,
            action="encounter.ai_generation_failed",
            resource_type="encounter",
            resource_id=encounter.id,
            patient_profile_id=encounter.patient_profile_id,
            encounter_id=encounter.id,
            details={"jobId": job.id, "error": error_message},
        )
    db.commit()
    if encounter:
        invalidate_patient_encounters(encounter.patient_profile_id)

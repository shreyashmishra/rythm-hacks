from __future__ import annotations

import os
import socket
import statistics
import subprocess
import tempfile
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from time import perf_counter

from redis import Redis
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import selectinload, sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///benchmark-bootstrap.db")
os.environ.setdefault("JWT_SECRET", "benchmark-secret")

from app.models import (  # noqa: E402
    DoctorProfile,
    Encounter,
    PatientProfile,
    Role,
    SuggestedTreatment,
    Symptom,
    User,
)
from app.routers.patients import get_serialized_patient_encounters  # noqa: E402
from app.serializers import serialize_encounter  # noqa: E402
from app.services.ehr_cache import (  # noqa: E402
    invalidate_patient_encounters,
    set_redis_client_for_testing,
)


TARGET_ENCOUNTERS = 800
BACKGROUND_PATIENTS = 24
BACKGROUND_ENCOUNTERS_PER_PATIENT = 18
SYMPTOMS_PER_ENCOUNTER = 6
TREATMENTS_PER_ENCOUNTER = 4
WARMUP_RUNS = 5
MEASURED_RUNS = 25


def build_engine():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "ehr-benchmark.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    return temp_dir, engine


def create_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def redis_server():
    temp_dir = tempfile.TemporaryDirectory()
    port = find_free_port()
    process = subprocess.Popen(
        [
            "redis-server",
            "--save",
            "",
            "--appendonly",
            "no",
            "--port",
            str(port),
            "--bind",
            "127.0.0.1",
            "--dir",
            temp_dir.name,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    client = Redis(
        host="127.0.0.1",
        port=port,
        db=0,
        decode_responses=True,
    )

    try:
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                client.ping()
                break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError("redis-server did not start in time")

        yield client
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        temp_dir.cleanup()


def seed_dataset(session_factory) -> str:
    session = session_factory()
    try:
        doctors = []
        for index in range(12):
            doctor_user = User(
                name=f"Doctor {index}",
                email=f"doctor{index}@example.com",
                password_hash="hash",
                role=Role.doctor,
            )
            doctor_profile = DoctorProfile(
                user=doctor_user,
                full_name=f"Doctor {index}",
                specialty="Internal Medicine",
            )
            doctors.append(doctor_profile)
            session.add(doctor_user)

        target_user = User(
            name="Target Patient",
            email="target.patient@example.com",
            password_hash="hash",
            role=Role.patient,
        )
        target_patient = PatientProfile(
            user=target_user,
            full_name="Target Patient",
            date_of_birth=date(1992, 4, 15),
            sex="female",
            allergies=["penicillin"],
            chronic_conditions=["asthma"],
            medications=["albuterol"],
            emergency_contact_name="Emergency Contact",
            emergency_contact_phone="555-0100",
        )
        session.add(target_user)

        start_time = datetime(2025, 1, 1, 9, 0, 0)
        for index in range(TARGET_ENCOUNTERS):
            doctor = doctors[index % len(doctors)]
            occurred_at = start_time + timedelta(hours=index)
            session.add(
                Encounter(
                    patient_profile=target_patient,
                    doctor_profile=doctor,
                    title=f"Follow-up visit {index}",
                    summary=(
                        "Detailed encounter note covering symptom progression, "
                        "observations, and clinician comments."
                    ),
                    ai_status="reviewed",
                    ai_disclaimer="Preliminary AI support only. Requires clinician review.",
                    ai_preliminary_summary=(
                        "Encounter may reflect a mild respiratory flare with stable vitals "
                        "and no immediate danger signs noted."
                    ),
                    ai_follow_up_window="within 2-3 days",
                    ai_clinical_considerations=[
                        "viral upper respiratory infection",
                        "asthma exacerbation",
                        "allergy-triggered symptoms",
                    ],
                    ai_red_flags=["worsening shortness of breath", "persistent fever"],
                    ai_follow_up_questions=[
                        "Has inhaler use increased in the last 48 hours?",
                        "Any chest tightness overnight?",
                    ],
                    ai_suggested_treatments=[
                        "hydration",
                        "rest",
                        "continue prescribed inhaler",
                    ],
                    ai_review_notes=(
                        "Doctor reviewed AI output, confirmed conservative plan, and "
                        "added follow-up instructions for symptom escalation."
                    ),
                    occurred_at=occurred_at,
                    symptoms=[
                        Symptom(name=f"symptom {symptom_index}")
                        for symptom_index in range(SYMPTOMS_PER_ENCOUNTER)
                    ],
                    suggested_treatments=[
                        SuggestedTreatment(name=f"treatment {treatment_index}")
                        for treatment_index in range(TREATMENTS_PER_ENCOUNTER)
                    ],
                )
            )

        for patient_index in range(BACKGROUND_PATIENTS):
            background_user = User(
                name=f"Background Patient {patient_index}",
                email=f"background{patient_index}@example.com",
                password_hash="hash",
                role=Role.patient,
            )
            background_patient = PatientProfile(
                user=background_user,
                full_name=f"Background Patient {patient_index}",
                date_of_birth=date(1988, 8, 20),
                sex="male",
            )
            session.add(background_user)

            for encounter_index in range(BACKGROUND_ENCOUNTERS_PER_PATIENT):
                session.add(
                    Encounter(
                        patient_profile=background_patient,
                        doctor_profile=doctors[(patient_index + encounter_index) % len(doctors)],
                        title=f"Background encounter {patient_index}-{encounter_index}",
                        summary="Background encounter note.",
                        ai_status="generated",
                        ai_disclaimer="Generated output pending review.",
                        ai_preliminary_summary="Background AI summary.",
                        ai_follow_up_window="within 1 week",
                        ai_clinical_considerations=["routine follow-up"],
                        ai_red_flags=[],
                        ai_follow_up_questions=[],
                        ai_suggested_treatments=["rest"],
                        ai_review_notes=None,
                        occurred_at=start_time + timedelta(days=patient_index, hours=encounter_index),
                        symptoms=[
                            Symptom(name=f"background symptom {symptom_index}")
                            for symptom_index in range(3)
                        ],
                        suggested_treatments=[SuggestedTreatment(name="background treatment")],
                    )
                )

        session.commit()
        return target_patient.id
    finally:
        session.close()


def baseline_fetch(session_factory, patient_profile_id: str) -> list[dict[str, object]]:
    session = session_factory()
    try:
        encounters = list(
            session.scalars(
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
        return [serialize_encounter(encounter) for encounter in encounters]
    finally:
        session.close()


def optimized_db_fetch(session_factory, patient_profile_id: str) -> list[dict[str, object]]:
    set_redis_client_for_testing(None)
    session = session_factory()
    try:
        return get_serialized_patient_encounters(session, patient_profile_id)
    finally:
        session.close()


def redis_cold_fetch(redis_client: Redis, session_factory, patient_profile_id: str) -> list[dict[str, object]]:
    set_redis_client_for_testing(redis_client)
    invalidate_patient_encounters(patient_profile_id)
    session = session_factory()
    try:
        return get_serialized_patient_encounters(session, patient_profile_id)
    finally:
        session.close()


def redis_warm_fetch(redis_client: Redis, session_factory, patient_profile_id: str) -> list[dict[str, object]]:
    set_redis_client_for_testing(redis_client)
    session = session_factory()
    try:
        return get_serialized_patient_encounters(session, patient_profile_id)
    finally:
        session.close()


@contextmanager
def count_queries(engine):
    state = {"count": 0}

    def before_cursor_execute(*_args, **_kwargs):
        state["count"] += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield state
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


def measure(label: str, fetch_fn) -> dict[str, float]:
    for _ in range(WARMUP_RUNS):
        payload = fetch_fn()
        if len(payload) != TARGET_ENCOUNTERS:
            raise RuntimeError(f"{label} returned {len(payload)} encounters, expected {TARGET_ENCOUNTERS}")

    timings = []
    for _ in range(MEASURED_RUNS):
        started_at = perf_counter()
        payload = fetch_fn()
        elapsed_ms = (perf_counter() - started_at) * 1000
        timings.append(elapsed_ms)
        if len(payload) != TARGET_ENCOUNTERS:
            raise RuntimeError(f"{label} returned {len(payload)} encounters, expected {TARGET_ENCOUNTERS}")

    return {
        "mean_ms": statistics.mean(timings),
        "median_ms": statistics.median(timings),
        "min_ms": min(timings),
        "max_ms": max(timings),
    }


def inspect_query_count(engine, fetch_fn) -> int:
    with count_queries(engine) as state:
        fetch_fn()
    return state["count"]


def print_stats(label: str, stats: dict[str, float], queries: int) -> None:
    print(
        f"{label:<13}: "
        f"mean={stats['mean_ms']:.2f} ms "
        f"median={stats['median_ms']:.2f} ms "
        f"queries={queries}"
    )


def main() -> None:
    temp_dir, engine = build_engine()
    try:
        from app.database import Base

        Base.metadata.create_all(bind=engine)
        session_factory = create_session_factory(engine)
        patient_profile_id = seed_dataset(session_factory)

        baseline_payload = baseline_fetch(session_factory, patient_profile_id)
        optimized_payload = optimized_db_fetch(session_factory, patient_profile_id)
        if baseline_payload != optimized_payload:
            raise RuntimeError("Optimized DB retrieval changed the serialized EHR payload")

        with redis_server() as redis_client:
            redis_client.flushall()
            redis_cold_payload = redis_cold_fetch(redis_client, session_factory, patient_profile_id)
            redis_warm_payload = redis_warm_fetch(redis_client, session_factory, patient_profile_id)
            if baseline_payload != redis_cold_payload or baseline_payload != redis_warm_payload:
                raise RuntimeError("Redis-backed retrieval changed the serialized EHR payload")

            baseline_stats = measure(
                "baseline",
                lambda: baseline_fetch(session_factory, patient_profile_id),
            )
            optimized_db_stats = measure(
                "optimized-db",
                lambda: optimized_db_fetch(session_factory, patient_profile_id),
            )
            redis_cold_stats = measure(
                "redis-cold",
                lambda: redis_cold_fetch(redis_client, session_factory, patient_profile_id),
            )

            redis_client.flushall()
            redis_warm_fetch(redis_client, session_factory, patient_profile_id)
            redis_warm_stats = measure(
                "redis-warm",
                lambda: redis_warm_fetch(redis_client, session_factory, patient_profile_id),
            )

            baseline_queries = inspect_query_count(
                engine,
                lambda: baseline_fetch(session_factory, patient_profile_id),
            )
            optimized_db_queries = inspect_query_count(
                engine,
                lambda: optimized_db_fetch(session_factory, patient_profile_id),
            )
            redis_cold_queries = inspect_query_count(
                engine,
                lambda: redis_cold_fetch(redis_client, session_factory, patient_profile_id),
            )
            redis_warm_queries = inspect_query_count(
                engine,
                lambda: redis_warm_fetch(redis_client, session_factory, patient_profile_id),
            )

            optimized_db_improvement = (
                (baseline_stats["mean_ms"] - optimized_db_stats["mean_ms"])
                / baseline_stats["mean_ms"]
            ) * 100
            redis_warm_improvement = (
                (baseline_stats["mean_ms"] - redis_warm_stats["mean_ms"])
                / baseline_stats["mean_ms"]
            ) * 100

            print("EHR retrieval benchmark")
            print(
                f"Dataset: {TARGET_ENCOUNTERS} target encounters, "
                f"{BACKGROUND_PATIENTS} background patients"
            )
            print_stats("Baseline", baseline_stats, baseline_queries)
            print_stats("Optimized DB", optimized_db_stats, optimized_db_queries)
            print_stats("Redis cold", redis_cold_stats, redis_cold_queries)
            print_stats("Redis warm", redis_warm_stats, redis_warm_queries)
            print(f"DB-only improvement   : {optimized_db_improvement:.2f}%")
            print(f"Redis warm improvement: {redis_warm_improvement:.2f}%")
    finally:
        set_redis_client_for_testing(None)
        temp_dir.cleanup()


if __name__ == "__main__":
    main()

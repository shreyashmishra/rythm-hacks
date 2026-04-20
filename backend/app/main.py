from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import inspect, text

from .config import settings
from .database import Base, engine
from .routers.auth import router as auth_router
from .routers.dashboard import router as dashboard_router
from .routers.patients import router as patients_router

app = FastAPI(title="Rythm API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_phase4_columns()
    ensure_auth_columns()
    ensure_performance_indexes()


def ensure_phase4_columns() -> None:
    inspector = inspect(engine)
    if "encounters" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("encounters")}
    required_columns = {
        "ai_status": "VARCHAR(32) NULL",
        "ai_disclaimer": "TEXT NULL",
        "ai_preliminary_summary": "TEXT NULL",
        "ai_follow_up_window": "VARCHAR(255) NULL",
        "ai_clinical_considerations": "JSON NULL",
        "ai_red_flags": "JSON NULL",
        "ai_follow_up_questions": "JSON NULL",
        "ai_suggested_treatments": "JSON NULL",
        "ai_review_notes": "TEXT NULL",
    }

    with engine.begin() as connection:
        for column_name, column_sql in required_columns.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                text(f"ALTER TABLE encounters ADD COLUMN {column_name} {column_sql}")
            )


def ensure_auth_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    required_columns = {
        "session_version": "INTEGER NOT NULL DEFAULT 0",
    }

    with engine.begin() as connection:
        for column_name, column_sql in required_columns.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                text(f"ALTER TABLE users ADD COLUMN {column_name} {column_sql}")
            )


def ensure_performance_indexes() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_indexes = {
        "encounters": {
            "ix_encounters_patient_profile_occurred_at": (
                "CREATE INDEX ix_encounters_patient_profile_occurred_at "
                "ON encounters (patient_profile_id, occurred_at)"
            ),
            "ix_encounters_doctor_profile_occurred_at": (
                "CREATE INDEX ix_encounters_doctor_profile_occurred_at "
                "ON encounters (doctor_profile_id, occurred_at)"
            ),
        },
        "symptoms": {
            "ix_symptoms_encounter_id": (
                "CREATE INDEX ix_symptoms_encounter_id ON symptoms (encounter_id)"
            ),
        },
        "suggested_treatments": {
            "ix_suggested_treatments_encounter_id": (
                "CREATE INDEX ix_suggested_treatments_encounter_id "
                "ON suggested_treatments (encounter_id)"
            ),
        },
    }

    with engine.begin() as connection:
        for table_name, indexes in required_indexes.items():
            if table_name not in existing_tables:
                continue

            existing_index_names = {
                index["name"] for index in inspector.get_indexes(table_name)
            }
            for index_name, create_sql in indexes.items():
                if index_name in existing_index_names:
                    continue
                connection.execute(text(create_sql))


@app.exception_handler(HTTPException)
def http_exception_handler(_request: Request, exception: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content={"message": str(exception.detail)},
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    _request: Request, exception: RequestValidationError
) -> JSONResponse:
    first_error = exception.errors()[0] if exception.errors() else None
    message = first_error.get("msg", "Invalid request payload") if first_error else "Invalid request payload"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": message},
    )


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(patients_router)

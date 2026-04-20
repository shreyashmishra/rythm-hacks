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

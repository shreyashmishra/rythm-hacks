from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def generate_id() -> str:
    return uuid.uuid4().hex


class Role(str, enum.Enum):
    doctor = "doctor"
    patient = "patient"


class EncounterAiStatus(str, enum.Enum):
    not_requested = "not_requested"
    queued = "queued"
    processing = "processing"
    generated = "generated"
    reviewed = "reviewed"
    failed = "failed"


class AiJobStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), index=True)
    session_version: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    patient_profile: Mapped[PatientProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    doctor_profile: Mapped[DoctorProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(64), nullable=True)
    allergies: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    chronic_conditions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    medications: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="patient_profile")
    encounters: Mapped[list[Encounter]] = relationship(
        back_populates="patient_profile", cascade="all, delete-orphan"
    )


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    specialty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="doctor_profile")
    encounters: Mapped[list[Encounter]] = relationship(
        back_populates="doctor_profile", cascade="all, delete-orphan"
    )


class Encounter(Base):
    __tablename__ = "encounters"
    __table_args__ = (
        Index("ix_encounters_patient_profile_occurred_at", "patient_profile_id", "occurred_at"),
        Index("ix_encounters_doctor_profile_occurred_at", "doctor_profile_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    patient_profile_id: Mapped[str] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True
    )
    doctor_profile_id: Mapped[str] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_status: Mapped[EncounterAiStatus] = mapped_column(
        Enum(EncounterAiStatus),
        default=EncounterAiStatus.not_requested,
        nullable=False,
    )
    ai_disclaimer: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_preliminary_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_follow_up_window: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ai_clinical_considerations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_red_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_follow_up_questions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_suggested_treatments: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ai_generated_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generated_follow_up_window: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    ai_generated_clinical_considerations: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    ai_generated_red_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_generated_follow_up_questions: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    ai_generated_suggested_treatments: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    ai_generated_follow_up_actions: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    ai_generated_urgency_score: Mapped[int | None] = mapped_column(nullable=True)
    ai_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ai_reviewed_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ai_approved_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_approved_follow_up_window: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    ai_approved_clinical_considerations: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    ai_approved_red_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_approved_follow_up_questions: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    ai_approved_suggested_treatments: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    ai_approved_follow_up_actions: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    ai_approved_urgency_score: Mapped[int | None] = mapped_column(nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    patient_profile: Mapped[PatientProfile] = relationship(back_populates="encounters")
    doctor_profile: Mapped[DoctorProfile] = relationship(back_populates="encounters")
    symptoms: Mapped[list[Symptom]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    suggested_treatments: Mapped[list[SuggestedTreatment]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    ai_jobs: Mapped[list[AiJob]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    reviewed_by_user: Mapped[User | None] = relationship(
        foreign_keys=[ai_reviewed_by_user_id]
    )


class AiJob(Base):
    __tablename__ = "ai_jobs"
    __table_args__ = (
        Index("ix_ai_jobs_encounter_created_at", "encounter_id", "created_at"),
        Index("ix_ai_jobs_patient_status", "patient_profile_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"), index=True
    )
    patient_profile_id: Mapped[str] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True
    )
    requested_by_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[AiJobStatus] = mapped_column(
        Enum(AiJobStatus), default=AiJobStatus.queued, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    encounter: Mapped[Encounter] = relationship(back_populates="ai_jobs")
    requested_by_user: Mapped[User] = relationship()


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_patient_created_at", "patient_profile_id", "created_at"),
        Index("ix_audit_events_encounter_created_at", "encounter_id", "created_at"),
        Index("ix_audit_events_actor_created_at", "actor_user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    patient_profile_id: Mapped[str | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True, nullable=True
    )
    encounter_id: Mapped[str | None] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(128), index=True)
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    details: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    actor_user: Mapped[User | None] = relationship()


class Symptom(Base):
    __tablename__ = "symptoms"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    encounter: Mapped[Encounter] = relationship(back_populates="symptoms")


class SuggestedTreatment(Base):
    __tablename__ = "suggested_treatments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    encounter: Mapped[Encounter] = relationship(back_populates="suggested_treatments")

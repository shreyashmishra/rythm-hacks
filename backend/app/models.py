from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def generate_id() -> str:
    return uuid.uuid4().hex


class Role(str, enum.Enum):
    doctor = "doctor"
    patient = "patient"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), index=True)
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

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    patient_profile_id: Mapped[str] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True
    )
    doctor_profile_id: Mapped[str] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_disclaimer: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_preliminary_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_follow_up_window: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ai_clinical_considerations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_red_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_follow_up_questions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_suggested_treatments: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class Symptom(Base):
    __tablename__ = "symptoms"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    encounter_id: Mapped[str] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    encounter: Mapped[Encounter] = relationship(back_populates="symptoms")


class SuggestedTreatment(Base):
    __tablename__ = "suggested_treatments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_id)
    encounter_id: Mapped[str] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    encounter: Mapped[Encounter] = relationship(back_populates="suggested_treatments")

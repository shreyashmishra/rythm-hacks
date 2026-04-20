from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BaseInputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)


class SignupRequest(BaseInputModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    role: Literal["doctor", "patient"]


class LoginRequest(BaseInputModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    role: Literal["doctor", "patient"]


class EncounterCreateRequest(BaseInputModel):
    title: str = Field(min_length=2, max_length=120)
    summary: str | None = Field(default=None, max_length=1000)
    occurred_at: datetime | None = Field(default=None, alias="occurredAt")
    symptoms: list[str] = Field(min_length=1, max_length=25)
    suggested_treatments: list[str] = Field(
        default_factory=list, max_length=25, alias="suggestedTreatments"
    )


class EncounterTreatmentUpdateRequest(BaseInputModel):
    suggested_treatments: list[str] = Field(
        default_factory=list, max_length=25, alias="suggestedTreatments"
    )


class AiSuggestionResponse(BaseModel):
    disclaimer: str = Field(
        description="A cautious disclaimer that this is not a final diagnosis."
    )
    preliminary_summary: str = Field(
        alias="preliminarySummary",
        min_length=20,
        max_length=600,
        description="Cautious, non-definitive clinical summary.",
    )
    recommended_follow_up_window: str = Field(
        alias="recommendedFollowUpWindow",
        min_length=3,
        max_length=120,
        description="A cautious suggested follow-up timeframe such as within 24 hours, within 1 week, or routine follow-up.",
    )
    clinical_considerations: list[str] = Field(
        alias="clinicalConsiderations",
        min_length=1,
        max_length=6,
        description="Possible medical considerations phrased cautiously.",
    )
    red_flags: list[str] = Field(
        alias="redFlags",
        default_factory=list,
        max_length=6,
        description="Symptoms or situations that warrant urgent clinician attention.",
    )
    follow_up_questions: list[str] = Field(
        alias="followUpQuestions",
        default_factory=list,
        max_length=6,
        description="Questions a clinician may want to clarify.",
    )
    suggested_treatments: list[str] = Field(
        alias="suggestedTreatments",
        default_factory=list,
        max_length=6,
        description="Preliminary, non-definitive care suggestions.",
    )

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class AiReviewUpdateRequest(BaseInputModel):
    preliminary_summary: str = Field(
        alias="preliminarySummary", min_length=20, max_length=600
    )
    recommended_follow_up_window: str = Field(
        alias="recommendedFollowUpWindow", min_length=3, max_length=120
    )
    clinical_considerations: list[str] = Field(
        alias="clinicalConsiderations", min_length=1, max_length=6
    )
    red_flags: list[str] = Field(alias="redFlags", default_factory=list, max_length=6)
    follow_up_questions: list[str] = Field(
        alias="followUpQuestions", default_factory=list, max_length=6
    )
    suggested_treatments: list[str] = Field(
        alias="suggestedTreatments", default_factory=list, max_length=6
    )
    review_notes: str | None = Field(alias="reviewNotes", default=None, max_length=800)

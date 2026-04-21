from google import genai
from google.genai import types

from ..config import settings
from ..models import Encounter, PatientProfile
from ..schemas import AiSuggestionResponse


SYSTEM_INSTRUCTION = """
You are a cautious clinical support assistant for a demo application.
Generate preliminary structured medical suggestions from encounter symptoms.
Do not provide a final diagnosis.
Use tentative language such as "may", "could", "might", and "consider".
Always include a clear disclaimer that this is not a final diagnosis and requires clinician review.
Keep treatments conservative and non-definitive.
Return structured output that can be validated and stored in typed backend fields.
Always provide a recommended follow-up window using practical language such as
"same day clinician review", "within 24 hours", "within 2-3 days", "within 1 week",
or "routine follow-up if symptoms persist".
Provide an urgency score from 1 to 5 where 5 means urgent clinician attention is warranted.
""".strip()


def _build_prompt(patient_profile: PatientProfile, encounter: Encounter) -> str:
    symptoms = ", ".join(symptom.name for symptom in encounter.symptoms) or "No symptoms provided"
    allergies = ", ".join(patient_profile.allergies or []) or "None recorded"
    chronic_conditions = ", ".join(patient_profile.chronic_conditions or []) or "None recorded"
    medications = ", ".join(patient_profile.medications or []) or "None recorded"

    return f"""
Patient profile:
- Full name: {patient_profile.full_name}
- Sex: {patient_profile.sex or "Not recorded"}
- Allergies: {allergies}
- Chronic conditions: {chronic_conditions}
- Current medications: {medications}

Encounter:
- Title: {encounter.title}
- Summary: {encounter.summary or "No summary recorded"}
- Symptoms: {symptoms}

Return cautious, preliminary structured guidance only.
""".strip()


class GeminiAiService:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate_preliminary_suggestions(
        self, patient_profile: PatientProfile, encounter: Encounter
    ) -> AiSuggestionResponse:
        prompt = _build_prompt(patient_profile, encounter)
        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=AiSuggestionResponse,
                temperature=0.2,
            ),
        )

        parsed = response.parsed
        if isinstance(parsed, AiSuggestionResponse):
            return parsed

        if isinstance(parsed, dict):
            return AiSuggestionResponse.model_validate(parsed)

        raise RuntimeError("Gemini returned an unexpected structured output")

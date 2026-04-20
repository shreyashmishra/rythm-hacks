export interface PatientProfile {
  id: string
  fullName: string
  dateOfBirth: string | null
  age: number | null
  sex: string | null
  allergies: string[]
  chronicConditions: string[]
  medications: string[]
  emergencyContactName: string | null
  emergencyContactPhone: string | null
}

export interface AiSuggestion {
  status: 'not_requested' | 'generated' | 'reviewed'
  disclaimer: string | null
  preliminarySummary: string | null
  recommendedFollowUpWindow: string | null
  clinicalConsiderations: string[]
  redFlags: string[]
  followUpQuestions: string[]
  suggestedTreatments: string[]
  reviewNotes: string | null
}

export interface EncounterHistoryItem {
  id: string
  title: string
  summary: string | null
  occurredAt: string
  doctorName: string
  symptoms: string[]
  suggestedTreatments: string[]
  ai: AiSuggestion
}

export interface EncounterFormValues {
  title: string
  summary: string
  occurredAt: string
  symptoms: string[]
  suggestedTreatments: string[]
}

export interface AiReviewValues {
  preliminarySummary: string
  recommendedFollowUpWindow: string
  clinicalConsiderations: string[]
  redFlags: string[]
  followUpQuestions: string[]
  suggestedTreatments: string[]
  reviewNotes: string
}

export interface PatientProfilePayload {
  patient: PatientProfile
}

export interface EncounterHistoryPayload {
  encounters: EncounterHistoryItem[]
}

export interface EncounterPayload {
  encounter: EncounterHistoryItem
}

export interface PatientDashboardPayload {
  title: string
  subtitle: string
  encounterCount: number
}

export interface DoctorDashboardPayload {
  title: string
  subtitle: string
  encounterCount: number
  patientCount: number
}

export interface DoctorPatientDirectoryItem {
  id: string
  fullName: string
  age: number | null
  sex: string | null
  lastEncounterAt: string | null
}

export interface DoctorPatientListPayload {
  patients: DoctorPatientDirectoryItem[]
}

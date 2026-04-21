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

export interface AiStructuredVersion {
  preliminarySummary: string | null
  recommendedFollowUpWindow: string | null
  clinicalConsiderations: string[]
  redFlags: string[]
  followUpQuestions: string[]
  followUpActions: string[]
  suggestedTreatments: string[]
  urgencyScore: number | null
}

export interface AiJob {
  id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  errorMessage: string | null
  createdAt: string
  startedAt: string | null
  completedAt: string | null
}

export interface AiSuggestion {
  status: 'not_requested' | 'queued' | 'processing' | 'generated' | 'reviewed' | 'failed'
  disclaimer: string | null
  generatedAt: string | null
  reviewedAt: string | null
  reviewedBy: {
    id: string
    name: string
    role: 'doctor' | 'patient'
  } | null
  generated: AiStructuredVersion | null
  approved: AiStructuredVersion | null
  current: AiStructuredVersion | null
  diff: {
    changedFields: string[]
    changeCount: number
  }
  reviewNotes: string | null
  job: AiJob | null
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
  followUpActions: string[]
  suggestedTreatments: string[]
  urgencyScore: number
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
  reviewedEncounterCount: number
}

export interface DoctorDashboardPayload {
  title: string
  subtitle: string
  encounterCount: number
  patientCount: number
  pendingAiReviewCount: number
  highRiskCount: number
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

export interface AuditActivityItem {
  id: string
  action: string
  resourceType: string
  resourceId: string | null
  createdAt: string
  details: Record<string, unknown>
  actor: {
    id: string
    name: string
    role: 'doctor' | 'patient'
  } | null
}

export interface ActivityPayload {
  activity: AuditActivityItem[]
}

export interface AiJobPayload {
  job: AiJob | null
  reusedExistingJob: boolean
}

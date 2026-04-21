import type { AuthFormValues, AuthPayload } from '../types/auth'
import type {
  ActivityPayload,
  AiJobPayload,
  AiReviewValues,
  DoctorDashboardPayload,
  DoctorPatientListPayload,
  EncounterFormValues,
  EncounterPayload,
  EncounterHistoryPayload,
  PatientDashboardPayload,
  PatientProfilePayload,
} from '../types/ehr'

const API_URL = import.meta.env.VITE_API_URL ?? '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  const data = (await response.json().catch(() => null)) as { message?: string } | null

  if (!response.ok) {
    throw new Error(data?.message ?? 'Request failed')
  }

  return data as T
}

export const api = {
  me: () => request<AuthPayload>('/auth/me'),
  login: (values: AuthFormValues) =>
    request<AuthPayload>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(values),
    }),
  signup: (values: AuthFormValues) =>
    request<AuthPayload>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(values),
    }),
  logout: () =>
    request<{ success: boolean }>('/auth/logout', {
      method: 'POST',
    }),
  patientDashboard: () => request<PatientDashboardPayload>('/patient/dashboard'),
  doctorDashboard: () => request<DoctorDashboardPayload>('/doctor/dashboard'),
  patientProfile: () => request<PatientProfilePayload>('/patient/profile/me'),
  patientEncounterHistory: () => request<EncounterHistoryPayload>('/patient/encounters/me'),
  patientActivity: () => request<ActivityPayload>('/patient/activity/me'),
  doctorPatients: () => request<DoctorPatientListPayload>('/doctor/patients'),
  doctorPatientProfile: (patientProfileId: string) =>
    request<PatientProfilePayload>(`/doctor/patients/${patientProfileId}`),
  doctorPatientEncounterHistory: (patientProfileId: string) =>
    request<EncounterHistoryPayload>(`/doctor/patients/${patientProfileId}/encounters`),
  doctorPatientActivity: (patientProfileId: string) =>
    request<ActivityPayload>(`/doctor/patients/${patientProfileId}/activity`),
  createDoctorEncounter: (patientProfileId: string, values: EncounterFormValues) =>
    request<EncounterPayload>(`/doctor/patients/${patientProfileId}/encounters`, {
      method: 'POST',
      body: JSON.stringify(values),
    }),
  updateEncounterTreatments: (encounterId: string, suggestedTreatments: string[]) =>
    request<EncounterPayload>(`/doctor/encounters/${encounterId}/treatments`, {
      method: 'PATCH',
      body: JSON.stringify({ suggestedTreatments }),
    }),
  generateEncounterAi: (encounterId: string) =>
    request<AiJobPayload>(`/doctor/encounters/${encounterId}/ai-generate`, {
      method: 'POST',
    }),
  latestEncounterAiJob: (encounterId: string) =>
    request<Pick<AiJobPayload, 'job'>>(`/doctor/encounters/${encounterId}/ai-job`),
  reviewEncounterAi: (encounterId: string, values: AiReviewValues) =>
    request<EncounterPayload>(`/doctor/encounters/${encounterId}/ai-review`, {
      method: 'PATCH',
      body: JSON.stringify(values),
    }),
}

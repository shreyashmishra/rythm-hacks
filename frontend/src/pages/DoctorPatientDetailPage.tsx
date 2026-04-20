import { Link, Navigate, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { AiSuggestionCard } from '../components/AiSuggestionCard'
import { DashboardShell } from '../components/DashboardShell'
import { EncounterForm } from '../components/EncounterForm'
import { EncounterHistoryList } from '../components/EncounterHistoryList'
import { PatientProfileCard } from '../components/PatientProfileCard'
import { api } from '../lib/api'
import type {
  AiReviewValues,
  EncounterFormValues,
  EncounterHistoryItem,
  PatientProfile,
} from '../types/ehr'

export function DoctorPatientDetailPage() {
  const { patientProfileId } = useParams<{ patientProfileId: string }>()
  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [encounters, setEncounters] = useState<EncounterHistoryItem[]>([])
  const [error, setError] = useState('')
  const [creatingEncounter, setCreatingEncounter] = useState(false)
  const [generatingAiEncounterId, setGeneratingAiEncounterId] = useState<string | null>(null)
  const [reviewingAiEncounterId, setReviewingAiEncounterId] = useState<string | null>(null)

  async function loadPatientDetail(activePatientProfileId: string) {
    const [profilePayload, encounterPayload] = await Promise.all([
      api.doctorPatientProfile(activePatientProfileId),
      api.doctorPatientEncounterHistory(activePatientProfileId),
    ])
    setProfile(profilePayload.patient)
    setEncounters(encounterPayload.encounters)
  }

  useEffect(() => {
    if (!patientProfileId) {
      return
    }

    loadPatientDetail(patientProfileId)
      .then(() => {
        setError('')
      })
      .catch((loadError) => {
        setError(
          loadError instanceof Error ? loadError.message : 'Unable to load patient detail',
        )
      })
  }, [patientProfileId])

  async function handleCreateEncounter(values: EncounterFormValues) {
    if (!patientProfileId) {
      return
    }

    setCreatingEncounter(true)

    try {
      await api.createDoctorEncounter(patientProfileId, values)
      const encounterPayload = await api.doctorPatientEncounterHistory(patientProfileId)
      setEncounters(encounterPayload.encounters)
      setError('')
    } finally {
      setCreatingEncounter(false)
    }
  }

  async function handleGenerateAi(encounterId: string) {
    if (!patientProfileId) {
      return
    }

    setGeneratingAiEncounterId(encounterId)
    try {
      await api.generateEncounterAi(encounterId)
      const encounterPayload = await api.doctorPatientEncounterHistory(patientProfileId)
      setEncounters(encounterPayload.encounters)
      setError('')
    } finally {
      setGeneratingAiEncounterId(null)
    }
  }

  async function handleReviewAi(encounterId: string, values: AiReviewValues) {
    if (!patientProfileId) {
      return
    }

    setReviewingAiEncounterId(encounterId)
    try {
      await api.reviewEncounterAi(encounterId, values)
      const encounterPayload = await api.doctorPatientEncounterHistory(patientProfileId)
      setEncounters(encounterPayload.encounters)
      setError('')
    } finally {
      setReviewingAiEncounterId(null)
    }
  }

  if (!patientProfileId) {
    return <Navigate replace to="/doctor/dashboard" />
  }

  return (
    <DashboardShell
      badge="Doctor Patient Detail"
      subtitle="Doctor-side patient detail page with encounter review, AI suggestions, and demo-ready review controls."
      title={profile?.fullName ?? 'Patient detail'}
      actions={
        <Link
          className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
          to="/doctor/dashboard"
        >
          Back to dashboard
        </Link>
      }
    >
      <div className="space-y-4">
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        {profile ? <PatientProfileCard profile={profile} subtitle="Doctor-side patient detail page" /> : null}
        <EncounterForm onSubmit={handleCreateEncounter} submitting={creatingEncounter} />
        <EncounterHistoryList
          description="Doctor-side encounter history with symptoms, treatments, and AI review"
          encounters={encounters}
          renderActions={(encounter) => (
            <div className="space-y-4">
              <AiSuggestionCard
                ai={encounter.ai}
                doctorMode
                generating={generatingAiEncounterId === encounter.id}
                onGenerate={() => handleGenerateAi(encounter.id)}
                onReview={(values) => handleReviewAi(encounter.id, values)}
                reviewing={reviewingAiEncounterId === encounter.id}
              />
            </div>
          )}
          title="Encounter history"
        />
      </div>
    </DashboardShell>
  )
}

import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { AiSuggestionCard } from '../components/AiSuggestionCard'
import { DashboardShell } from '../components/DashboardShell'
import { EncounterHistoryList } from '../components/EncounterHistoryList'
import { PatientProfileCard } from '../components/PatientProfileCard'
import { api } from '../lib/api'
import type { EncounterHistoryItem, PatientProfile } from '../types/ehr'

export function PatientProfilePage() {
  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [encounters, setEncounters] = useState<EncounterHistoryItem[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.patientProfile(), api.patientEncounterHistory()])
      .then(([profilePayload, encounterPayload]) => {
        setProfile(profilePayload.patient)
        setEncounters(encounterPayload.encounters)
        setError('')
      })
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : 'Unable to load patient profile')
      })
  }, [])

  return (
    <DashboardShell
      badge="Patient Profile"
      subtitle="Patient-side profile page with the visible profile card and encounter history."
      title="My profile"
      actions={
        <Link
          className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
          to="/patient/dashboard"
        >
          Back to dashboard
        </Link>
      }
    >
      <div className="space-y-4">
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        {profile ? <PatientProfileCard profile={profile} subtitle="Patient-side profile page" /> : null}
        <EncounterHistoryList
          description="Encounter history list view with symptoms, suggested treatments, and AI support notes"
          encounters={encounters}
          renderActions={(encounter) => <AiSuggestionCard ai={encounter.ai} />}
          title="Encounter history"
        />
      </div>
    </DashboardShell>
  )
}

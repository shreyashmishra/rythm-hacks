import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { AiSuggestionCard } from '../components/AiSuggestionCard'
import { DashboardShell } from '../components/DashboardShell'
import { EncounterHistoryList } from '../components/EncounterHistoryList'
import { PatientProfileCard } from '../components/PatientProfileCard'
import { api } from '../lib/api'
import type { EncounterHistoryItem, PatientDashboardPayload, PatientProfile } from '../types/ehr'

export function PatientDashboardPage() {
  const [summary, setSummary] = useState<PatientDashboardPayload | null>(null)
  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [encounters, setEncounters] = useState<EncounterHistoryItem[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.patientDashboard(),
      api.patientProfile(),
      api.patientEncounterHistory(),
    ])
      .then(([dashboardPayload, profilePayload, encounterPayload]) => {
        setSummary(dashboardPayload)
        setProfile(profilePayload.patient)
        setEncounters(encounterPayload.encounters)
        setError('')
      })
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : 'Unable to load dashboard')
      })
  }, [])

  return (
    <DashboardShell
      badge="Patient Dashboard"
      subtitle={summary?.subtitle ?? 'Loading patient record...'}
      title={summary?.title ?? 'Patient dashboard'}
      actions={
        <Link
          className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
          to="/patient/profile"
        >
          Open profile page
        </Link>
      }
    >
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <div className="space-y-4">
        {profile ? <PatientProfileCard profile={profile} subtitle="Patient profile section" /> : null}
        <div className="grid gap-4 md:grid-cols-3">
          <article className="rounded-3xl border border-line bg-slate-50 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Encounters</p>
            <h2 className="mt-3 text-3xl font-semibold text-ink">{summary?.encounterCount ?? 0}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">Recorded visits in your history.</p>
          </article>
          <article className="rounded-3xl border border-line bg-slate-50 p-5 md:col-span-2">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Scope</p>
            <h2 className="mt-3 text-lg font-semibold text-ink">Demo-ready AI support view</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Encounter cards now include preliminary AI guidance, but all language remains
              cautious and explicitly non-definitive.
            </p>
          </article>
        </div>
        <EncounterHistoryList
          description="Patient-side list view with symptoms, suggested treatments, and AI support notes"
          encounters={encounters}
          renderActions={(encounter) => <AiSuggestionCard ai={encounter.ai} />}
          title="Encounter history"
        />
      </div>
    </DashboardShell>
  )
}

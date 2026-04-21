import { useDeferredValue, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { DashboardShell } from '../components/DashboardShell'
import { EmptyState } from '../components/EmptyState'
import { InputField } from '../components/InputField'
import { api } from '../lib/api'
import { formatAge, formatDate, formatLabel } from '../lib/formatters'
import type { DoctorDashboardPayload, DoctorPatientDirectoryItem } from '../types/ehr'

export function DoctorDashboardPage() {
  const [summary, setSummary] = useState<DoctorDashboardPayload | null>(null)
  const [patients, setPatients] = useState<DoctorPatientDirectoryItem[]>([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const deferredSearch = useDeferredValue(search)

  useEffect(() => {
    Promise.all([api.doctorDashboard(), api.doctorPatients()])
      .then(([dashboardPayload, patientPayload]) => {
        setSummary(dashboardPayload)
        setPatients(patientPayload.patients)
        setError('')
      })
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : 'Unable to load dashboard')
      })
  }, [])

  const filteredPatients = patients.filter((patient) =>
    patient.fullName.toLowerCase().includes(deferredSearch.trim().toLowerCase()),
  )

  return (
    <DashboardShell
      badge="Doctor Dashboard"
      subtitle={summary?.subtitle ?? 'Loading doctor workspace...'}
      title={summary?.title ?? 'Doctor dashboard'}
    >
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <article className="rounded-3xl border border-line bg-slate-50 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Patients</p>
            <h2 className="mt-3 text-3xl font-semibold text-ink">{summary?.patientCount ?? 0}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">Profiles available to review.</p>
          </article>
          <article className="rounded-3xl border border-line bg-slate-50 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Encounters</p>
            <h2 className="mt-3 text-3xl font-semibold text-ink">{summary?.encounterCount ?? 0}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">Encounters linked to your doctor profile.</p>
          </article>
          <article className="rounded-3xl border border-line bg-slate-50 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Pending AI review</p>
            <h2 className="mt-3 text-3xl font-semibold text-ink">
              {summary?.pendingAiReviewCount ?? 0}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Drafts still queued, generating, or awaiting doctor approval.
            </p>
          </article>
          <article className="rounded-3xl border border-line bg-slate-50 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Higher risk</p>
            <h2 className="mt-3 text-3xl font-semibold text-ink">{summary?.highRiskCount ?? 0}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Encounters with urgency scores of 4 or 5.
            </p>
          </article>
        </div>

        {patients.length === 0 ? (
          <EmptyState
            description="Patient accounts will appear here once they exist in the system."
            title="Patient directory"
          />
        ) : (
          <section className="rounded-[28px] border border-line bg-white p-6">
            <div className="border-b border-line pb-5">
              <p className="text-xs uppercase tracking-[0.2em] text-accent">Protected clinician workspace</p>
              <h2 className="mt-3 text-2xl font-semibold text-ink">Patient directory</h2>
              <div className="mt-4 max-w-md">
                <InputField
                  label="Search patients"
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search by full name"
                  value={search}
                />
              </div>
            </div>
            <div className="mt-5 space-y-3">
              {filteredPatients.length === 0 ? (
                <EmptyState
                  description="No patient matches the current search."
                  title="No search results"
                />
              ) : null}
              {filteredPatients.map((patient) => (
                <article
                  className="flex flex-col gap-4 rounded-3xl border border-line bg-slate-50 p-5 md:flex-row md:items-center md:justify-between"
                  key={patient.id}
                >
                  <div>
                    <h3 className="text-lg font-semibold text-ink">{patient.fullName}</h3>
                    <p className="mt-1 text-sm text-slate-500">
                      {formatAge(patient.age)} · {formatLabel(patient.sex)}
                    </p>
                    <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                      Last encounter: {formatDate(patient.lastEncounterAt)}
                    </p>
                  </div>
                  <Link
                    className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
                    to={`/doctor/patients/${patient.id}`}
                  >
                    Open detail page
                  </Link>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>
    </DashboardShell>
  )
}

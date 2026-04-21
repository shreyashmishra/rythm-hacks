import { useEffect, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'

import { AiSuggestionCard } from '../components/AiSuggestionCard'
import { AuditActivityPanel } from '../components/AuditActivityPanel'
import { DashboardShell } from '../components/DashboardShell'
import { EncounterForm } from '../components/EncounterForm'
import { EncounterHistoryList } from '../components/EncounterHistoryList'
import { PatientProfileCard } from '../components/PatientProfileCard'
import { api } from '../lib/api'
import type {
  AiReviewValues,
  AuditActivityItem,
  EncounterFormValues,
  EncounterHistoryItem,
  PatientProfile,
} from '../types/ehr'

export function DoctorPatientDetailPage() {
  const { patientProfileId } = useParams<{ patientProfileId: string }>()
  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [encounters, setEncounters] = useState<EncounterHistoryItem[]>([])
  const [activity, setActivity] = useState<AuditActivityItem[]>([])
  const [error, setError] = useState('')
  const [creatingEncounter, setCreatingEncounter] = useState(false)
  const [generatingAiEncounterId, setGeneratingAiEncounterId] = useState<string | null>(null)
  const [reviewingAiEncounterId, setReviewingAiEncounterId] = useState<string | null>(null)

  async function loadPatientDetail(activePatientProfileId: string) {
    const [profilePayload, encounterPayload, activityPayload] = await Promise.all([
      api.doctorPatientProfile(activePatientProfileId),
      api.doctorPatientEncounterHistory(activePatientProfileId),
      api.doctorPatientActivity(activePatientProfileId),
    ])
    setProfile(profilePayload.patient)
    setEncounters(encounterPayload.encounters)
    setActivity(activityPayload.activity)
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

  const hasActiveAiJobs = encounters.some(
    (encounter) =>
      encounter.ai.status === 'queued' || encounter.ai.status === 'processing',
  )

  useEffect(() => {
    if (!patientProfileId || !hasActiveAiJobs) {
      return
    }

    const intervalId = window.setInterval(() => {
      const activeEncounterIds = encounters
        .filter(
          (encounter) =>
            encounter.ai.status === 'queued' || encounter.ai.status === 'processing',
        )
        .map((encounter) => encounter.id)

      void Promise.all(activeEncounterIds.map((encounterId) => api.latestEncounterAiJob(encounterId)))
        .then((jobPayloads) => {
          const latestJobsByEncounterId = new Map(
            activeEncounterIds.map((encounterId, index) => [encounterId, jobPayloads[index].job]),
          )
          const hasCompletedJob = jobPayloads.some((payload) => {
            const status = payload.job?.status
            return status === 'completed' || status === 'failed' || payload.job === null
          })

          if (hasCompletedJob) {
            void loadPatientDetail(patientProfileId).catch(() => undefined)
            return
          }

          setEncounters((currentEncounters) =>
            currentEncounters.map((encounter) => {
              const latestJob = latestJobsByEncounterId.get(encounter.id)
              if (!latestJob) {
                return encounter
              }

              return {
                ...encounter,
                ai: {
                  ...encounter.ai,
                  status: latestJob.status === 'completed' ? 'generated' : latestJob.status,
                  job: latestJob,
                },
              }
            }),
          )
        })
        .catch(() => undefined)
    }, 2000)

    return () => window.clearInterval(intervalId)
  }, [encounters, hasActiveAiJobs, patientProfileId])

  async function handleCreateEncounter(values: EncounterFormValues) {
    if (!patientProfileId) {
      return
    }

    setCreatingEncounter(true)

    try {
      await api.createDoctorEncounter(patientProfileId, values)
      await loadPatientDetail(patientProfileId)
      setError('')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Unable to save encounter')
      throw submitError
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
      await loadPatientDetail(patientProfileId)
      setError('')
    } catch (generateError) {
      setError(
        generateError instanceof Error ? generateError.message : 'Unable to queue AI draft',
      )
      throw generateError
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
      await loadPatientDetail(patientProfileId)
      setError('')
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : 'Unable to approve AI note')
      throw reviewError
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
      subtitle="Owner-scoped encounter editing, async AI drafts, doctor approval, and audit activity."
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
        {profile ? (
          <PatientProfileCard
            profile={profile}
            subtitle="Protected patient record visible to doctor workflows only"
          />
        ) : null}
        <EncounterForm onSubmit={handleCreateEncounter} submitting={creatingEncounter} />
        <EncounterHistoryList
          description="Timeline of encounters with structured AI draft state and doctor approval"
          encounters={encounters}
          renderActions={(encounter) => (
            <AiSuggestionCard
              ai={encounter.ai}
              doctorMode
              generating={generatingAiEncounterId === encounter.id}
              onGenerate={() => handleGenerateAi(encounter.id)}
              onReview={(values) => handleReviewAi(encounter.id, values)}
              reviewing={reviewingAiEncounterId === encounter.id}
            />
          )}
          title="Encounter timeline"
        />
        <AuditActivityPanel
          activity={activity}
          description="Read/write audit trail for this patient record"
          title="Audit activity"
        />
      </div>
    </DashboardShell>
  )
}

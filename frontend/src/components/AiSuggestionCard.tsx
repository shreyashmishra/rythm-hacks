import { useState } from 'react'

import type { AiReviewValues, AiStructuredVersion, AiSuggestion } from '../types/ehr'
import { InputField } from './InputField'
import { StringListEditor } from './StringListEditor'
import { TextAreaField } from './TextAreaField'

function ReadOnlyList({
  title,
  items,
  emptyLabel,
}: {
  title: string
  items: string[]
  emptyLabel: string
}) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">{title}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.length === 0 ? (
          <span className="text-sm text-slate-400">{emptyLabel}</span>
        ) : (
          items.map((item) => (
            <span className="rounded-full bg-white px-3 py-1 text-sm text-slate-700" key={item}>
              {item}
            </span>
          ))
        )}
      </div>
    </div>
  )
}

function statusLabel(status: AiSuggestion['status']) {
  switch (status) {
    case 'queued':
      return 'AI draft queued'
    case 'processing':
      return 'AI draft processing'
    case 'generated':
      return 'AI draft ready for review'
    case 'reviewed':
      return 'Doctor-approved note'
    case 'failed':
      return 'AI generation failed'
    default:
      return 'AI not generated'
  }
}

function diffFieldLabel(fieldName: string) {
  const labels: Record<string, string> = {
    preliminarySummary: 'Summary',
    recommendedFollowUpWindow: 'Follow-up window',
    clinicalConsiderations: 'Clinical considerations',
    redFlags: 'Flagged risks',
    followUpQuestions: 'Follow-up questions',
    followUpActions: 'Follow-up actions',
    suggestedTreatments: 'Suggested treatments',
    urgencyScore: 'Urgency score',
  }

  return labels[fieldName] ?? fieldName
}

function VersionPanel({
  title,
  subtitle,
  version,
}: {
  title: string
  subtitle: string
  version: AiStructuredVersion | null
}) {
  if (!version) {
    return null
  }

  return (
    <div className="rounded-2xl border border-line bg-white/80 p-4">
      <p className="text-[11px] uppercase tracking-[0.2em] text-accent">{subtitle}</p>
      <h5 className="mt-2 text-base font-semibold text-ink">{title}</h5>

      <div className="mt-4 space-y-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Summary</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {version.preliminarySummary ?? 'No summary recorded.'}
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Follow-up window
            </p>
            <p className="mt-2 text-sm font-medium text-ink">
              {version.recommendedFollowUpWindow ?? 'No follow-up window recorded.'}
            </p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Urgency score</p>
            <p className="mt-2 text-sm font-medium text-ink">
              {version.urgencyScore ?? 'Not scored'} / 5
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <ReadOnlyList
            emptyLabel="No clinical considerations recorded."
            items={version.clinicalConsiderations}
            title="Clinical considerations"
          />
          <ReadOnlyList
            emptyLabel="No risks recorded."
            items={version.redFlags}
            title="Flagged risks"
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <ReadOnlyList
            emptyLabel="No follow-up questions recorded."
            items={version.followUpQuestions}
            title="Follow-up questions"
          />
          <ReadOnlyList
            emptyLabel="No follow-up actions recorded."
            items={version.followUpActions}
            title="Follow-up actions"
          />
        </div>

        <ReadOnlyList
          emptyLabel="No suggested treatments recorded."
          items={version.suggestedTreatments}
          title="Suggested treatments"
        />
      </div>
    </div>
  )
}

export function AiSuggestionCard({
  ai,
  doctorMode = false,
  generating = false,
  reviewing = false,
  onGenerate,
  onReview,
}: {
  ai: AiSuggestion
  doctorMode?: boolean
  generating?: boolean
  reviewing?: boolean
  onGenerate?: () => Promise<void>
  onReview?: (values: AiReviewValues) => Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const draft = ai.approved ?? ai.generated ?? ai.current
  const [preliminarySummary, setPreliminarySummary] = useState(draft?.preliminarySummary ?? '')
  const [recommendedFollowUpWindow, setRecommendedFollowUpWindow] = useState(
    draft?.recommendedFollowUpWindow ?? '',
  )
  const [clinicalConsiderations, setClinicalConsiderations] = useState(
    draft?.clinicalConsiderations ?? [],
  )
  const [redFlags, setRedFlags] = useState(draft?.redFlags ?? [])
  const [followUpQuestions, setFollowUpQuestions] = useState(draft?.followUpQuestions ?? [])
  const [followUpActions, setFollowUpActions] = useState(draft?.followUpActions ?? [])
  const [suggestedTreatments, setSuggestedTreatments] = useState(draft?.suggestedTreatments ?? [])
  const [urgencyScore, setUrgencyScore] = useState(draft?.urgencyScore?.toString() ?? '3')
  const [reviewNotes, setReviewNotes] = useState(ai.reviewNotes ?? '')
  const [error, setError] = useState('')

  function openReview() {
    const activeDraft = ai.approved ?? ai.generated ?? ai.current
    setPreliminarySummary(activeDraft?.preliminarySummary ?? '')
    setRecommendedFollowUpWindow(activeDraft?.recommendedFollowUpWindow ?? '')
    setClinicalConsiderations(activeDraft?.clinicalConsiderations ?? [])
    setRedFlags(activeDraft?.redFlags ?? [])
    setFollowUpQuestions(activeDraft?.followUpQuestions ?? [])
    setFollowUpActions(activeDraft?.followUpActions ?? [])
    setSuggestedTreatments(activeDraft?.suggestedTreatments ?? [])
    setUrgencyScore(activeDraft?.urgencyScore?.toString() ?? '3')
    setReviewNotes(ai.reviewNotes ?? '')
    setError('')
    setEditing(true)
  }

  async function handleReviewSave() {
    if (!onReview) {
      return
    }

    const parsedUrgencyScore = Number(urgencyScore)

    if (preliminarySummary.trim().length < 20) {
      setError('Summary should be at least 20 characters.')
      return
    }

    if (recommendedFollowUpWindow.trim().length < 3) {
      setError('Recommended follow-up window is required.')
      return
    }

    if (clinicalConsiderations.length === 0) {
      setError('Add at least one clinical consideration before approving.')
      return
    }

    if (!Number.isInteger(parsedUrgencyScore) || parsedUrgencyScore < 1 || parsedUrgencyScore > 5) {
      setError('Urgency score must be an integer between 1 and 5.')
      return
    }

    try {
      setError('')
      await onReview({
        preliminarySummary: preliminarySummary.trim(),
        recommendedFollowUpWindow: recommendedFollowUpWindow.trim(),
        clinicalConsiderations,
        redFlags,
        followUpQuestions,
        followUpActions,
        suggestedTreatments,
        urgencyScore: parsedUrgencyScore,
        reviewNotes: reviewNotes.trim(),
      })
      setEditing(false)
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save AI review')
    }
  }

  const jobIsActive = ai.job?.status === 'queued' || ai.job?.status === 'processing'

  return (
    <section className="rounded-3xl border border-teal-200 bg-gradient-to-br from-teal-50 via-white to-slate-50 p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent">AI draft review</p>
          <h4 className="mt-2 text-lg font-semibold text-ink">{statusLabel(ai.status)}</h4>
        </div>
        {doctorMode && onGenerate ? (
          <button
            className="rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
            disabled={generating || jobIsActive}
            onClick={() => void onGenerate()}
            type="button"
          >
            {generating || jobIsActive
              ? 'AI job running...'
              : ai.status === 'not_requested'
                ? 'Queue AI draft'
                : 'Regenerate AI draft'}
          </button>
        ) : null}
      </div>

      <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
        {ai.disclaimer ??
          'Preliminary AI support only. This is not a final diagnosis and requires clinician review.'}
      </div>

      {ai.job ? (
        <div className="mt-4 rounded-2xl border border-line bg-white px-4 py-3 text-sm text-slate-600">
          Latest job: <span className="font-semibold text-ink">{ai.job.status}</span>
          {ai.job.errorMessage ? <span className="text-rose-600"> · {ai.job.errorMessage}</span> : null}
        </div>
      ) : null}

      {ai.status === 'not_requested' ? (
        <p className="mt-4 text-sm text-slate-500">
          No AI output has been generated for this encounter yet.
        </p>
      ) : null}

      {ai.status === 'failed' ? (
        <p className="mt-4 text-sm text-rose-600">
          The last AI generation job failed. Regenerate the draft to try again.
        </p>
      ) : null}

      {ai.status !== 'not_requested' && !editing ? (
        <div className="mt-4 space-y-4">
          <VersionPanel
            subtitle="Structured Gemini output"
            title="Generated draft"
            version={ai.generated}
          />

          {ai.approved ? (
            <VersionPanel
              subtitle="Doctor-in-the-loop approval"
              title="Approved note"
              version={ai.approved}
            />
          ) : null}

          {ai.reviewedBy || ai.reviewedAt ? (
            <div className="rounded-2xl border border-line bg-white px-4 py-3 text-sm text-slate-600">
              Approved by {ai.reviewedBy?.name ?? 'Unknown reviewer'}
              {ai.reviewedAt ? ` on ${new Date(ai.reviewedAt).toLocaleString()}` : null}
            </div>
          ) : null}

          {ai.diff.changeCount > 0 ? (
            <div>
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
                Doctor changes from AI draft
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {ai.diff.changedFields.map((fieldName) => (
                  <span
                    className="rounded-full bg-teal-100 px-3 py-1 text-sm text-teal-800"
                    key={fieldName}
                  >
                    {diffFieldLabel(fieldName)}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {ai.reviewNotes ? (
            <div>
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
                Doctor review notes
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-700">{ai.reviewNotes}</p>
            </div>
          ) : null}

          {doctorMode && onReview && ai.generated ? (
            <button
              className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
              onClick={openReview}
              type="button"
            >
              {ai.approved ? 'Update approved note' : 'Review and approve'}
            </button>
          ) : null}
        </div>
      ) : null}

      {editing ? (
        <div className="mt-4 space-y-4">
          <TextAreaField
            label="Approved summary"
            onChange={(event) => setPreliminarySummary(event.target.value)}
            value={preliminarySummary}
          />
          <TextAreaField
            label="Recommended follow-up window"
            onChange={(event) => setRecommendedFollowUpWindow(event.target.value)}
            placeholder="Within 24-48 hours if symptoms persist or worsen."
            value={recommendedFollowUpWindow}
          />
          <StringListEditor
            buttonLabel="Add consideration"
            label="Clinical considerations"
            onChange={setClinicalConsiderations}
            placeholder="Could be related to a viral upper respiratory process"
            values={clinicalConsiderations}
          />
          <StringListEditor
            buttonLabel="Add risk"
            label="Flagged risks"
            onChange={setRedFlags}
            placeholder="Worsening shortness of breath"
            values={redFlags}
          />
          <StringListEditor
            buttonLabel="Add question"
            label="Follow-up questions"
            onChange={setFollowUpQuestions}
            placeholder="How long have symptoms been present?"
            values={followUpQuestions}
          />
          <StringListEditor
            buttonLabel="Add follow-up action"
            label="Follow-up actions"
            onChange={setFollowUpActions}
            placeholder="Book a primary care follow-up this week"
            values={followUpActions}
          />
          <StringListEditor
            buttonLabel="Add treatment"
            helperText="These values become the approved encounter treatment plan."
            label="Suggested treatments"
            onChange={setSuggestedTreatments}
            placeholder="Hydration"
            values={suggestedTreatments}
          />
          <InputField
            label="Urgency score (1-5)"
            max="5"
            min="1"
            onChange={(event) => setUrgencyScore(event.target.value)}
            placeholder="3"
            type="number"
            value={urgencyScore}
          />
          <TextAreaField
            label="Doctor review notes"
            onChange={(event) => setReviewNotes(event.target.value)}
            placeholder="Optional note describing what changed from the AI draft."
            value={reviewNotes}
          />
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          <div className="flex gap-2">
            <button
              className="rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={reviewing}
              onClick={() => void handleReviewSave()}
              type="button"
            >
              {reviewing ? 'Approving...' : 'Approve reviewed note'}
            </button>
            <button
              className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
              onClick={() => setEditing(false)}
              type="button"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </section>
  )
}

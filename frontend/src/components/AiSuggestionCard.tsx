import { useState } from 'react'

import type { AiReviewValues, AiSuggestion } from '../types/ehr'
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
  if (status === 'reviewed') {
    return 'Doctor reviewed'
  }

  if (status === 'generated') {
    return 'Preliminary AI output'
  }

  return 'AI not generated'
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
  const [preliminarySummary, setPreliminarySummary] = useState(ai.preliminarySummary ?? '')
  const [recommendedFollowUpWindow, setRecommendedFollowUpWindow] = useState(
    ai.recommendedFollowUpWindow ?? '',
  )
  const [clinicalConsiderations, setClinicalConsiderations] = useState(ai.clinicalConsiderations)
  const [redFlags, setRedFlags] = useState(ai.redFlags)
  const [followUpQuestions, setFollowUpQuestions] = useState(ai.followUpQuestions)
  const [suggestedTreatments, setSuggestedTreatments] = useState(ai.suggestedTreatments)
  const [reviewNotes, setReviewNotes] = useState(ai.reviewNotes ?? '')
  const [error, setError] = useState('')

  function openReview() {
    setPreliminarySummary(ai.preliminarySummary ?? '')
    setRecommendedFollowUpWindow(ai.recommendedFollowUpWindow ?? '')
    setClinicalConsiderations(ai.clinicalConsiderations)
    setRedFlags(ai.redFlags)
    setFollowUpQuestions(ai.followUpQuestions)
    setSuggestedTreatments(ai.suggestedTreatments)
    setReviewNotes(ai.reviewNotes ?? '')
    setError('')
    setEditing(true)
  }

  async function handleReviewSave() {
    if (!onReview) {
      return
    }

    if (preliminarySummary.trim().length < 20) {
      setError('Preliminary summary should be at least 20 characters.')
      return
    }

    if (recommendedFollowUpWindow.trim().length < 3) {
      setError('Recommended follow-up window is required.')
      return
    }

    if (clinicalConsiderations.length === 0) {
      setError('Add at least one clinical consideration before finalizing.')
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
        suggestedTreatments,
        reviewNotes: reviewNotes.trim(),
      })
      setEditing(false)
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save AI review')
    }
  }

  return (
    <section className="rounded-3xl border border-teal-200 bg-gradient-to-br from-teal-50 via-white to-slate-50 p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent">AI suggestion review</p>
          <h4 className="mt-2 text-lg font-semibold text-ink">{statusLabel(ai.status)}</h4>
        </div>
        {doctorMode && onGenerate ? (
          <button
            className="rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
            disabled={generating}
            onClick={() => void onGenerate()}
            type="button"
          >
            {generating ? 'Generating...' : ai.status === 'not_requested' ? 'Generate AI suggestions' : 'Regenerate AI suggestions'}
          </button>
        ) : null}
      </div>

      <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
        {ai.disclaimer ?? 'Preliminary AI support only. This is not a final diagnosis and requires clinician review.'}
      </div>

      {ai.status === 'not_requested' ? (
        <p className="mt-4 text-sm text-slate-500">
          No AI output has been generated for this encounter yet.
        </p>
      ) : null}

      {ai.status !== 'not_requested' && !editing ? (
        <div className="mt-4 space-y-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Preliminary summary</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {ai.preliminarySummary ?? 'No AI summary available.'}
            </p>
          </div>

          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Recommended follow-up window
            </p>
            <p className="mt-2 text-sm font-medium leading-6 text-ink">
              {ai.recommendedFollowUpWindow ?? 'No follow-up window recorded.'}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <ReadOnlyList
              emptyLabel="No clinical considerations recorded."
              items={ai.clinicalConsiderations}
              title="Clinical considerations"
            />
            <ReadOnlyList
              emptyLabel="No red flags recorded."
              items={ai.redFlags}
              title="Red flags"
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <ReadOnlyList
              emptyLabel="No follow-up questions recorded."
              items={ai.followUpQuestions}
              title="Follow-up questions"
            />
            <ReadOnlyList
              emptyLabel="No AI suggested treatments recorded."
              items={ai.suggestedTreatments}
              title="AI suggested treatments"
            />
          </div>

          {ai.reviewNotes ? (
            <div>
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Doctor review notes</p>
              <p className="mt-2 text-sm leading-6 text-slate-700">{ai.reviewNotes}</p>
            </div>
          ) : null}

          {doctorMode && onReview ? (
            <button
              className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
              onClick={openReview}
              type="button"
            >
              Review and finalize
            </button>
          ) : null}
        </div>
      ) : null}

      {editing ? (
        <div className="mt-4 space-y-4">
          <TextAreaField
            label="Preliminary summary"
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
            buttonLabel="Add red flag"
            label="Red flags"
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
            buttonLabel="Add treatment"
            helperText="These values will become the finalized encounter suggested treatments."
            label="Suggested treatments"
            onChange={setSuggestedTreatments}
            placeholder="Hydration"
            values={suggestedTreatments}
          />
          <TextAreaField
            label="Doctor review notes"
            onChange={(event) => setReviewNotes(event.target.value)}
            placeholder="Optional note about what was accepted, changed, or rejected."
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
              {reviewing ? 'Finalizing...' : 'Finalize AI review'}
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

import { useState, type FormEvent } from 'react'

import type { EncounterFormValues } from '../types/ehr'
import { InputField } from './InputField'
import { StringListEditor } from './StringListEditor'
import { TextAreaField } from './TextAreaField'

export function EncounterForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (values: EncounterFormValues) => Promise<void>
  submitting: boolean
}) {
  const [title, setTitle] = useState('')
  const [occurredAt, setOccurredAt] = useState('')
  const [summary, setSummary] = useState('')
  const [symptoms, setSymptoms] = useState<string[]>([])
  const [suggestedTreatments, setSuggestedTreatments] = useState<string[]>([])
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (title.trim().length < 2) {
      setError('Encounter title must be at least 2 characters.')
      return
    }

    if (symptoms.length === 0) {
      setError('Add at least one symptom before saving the encounter.')
      return
    }

    try {
      setError('')
      await onSubmit({
        title: title.trim(),
        summary: summary.trim(),
        occurredAt: occurredAt ? new Date(occurredAt).toISOString() : '',
        symptoms,
        suggestedTreatments,
      })
      setTitle('')
      setOccurredAt('')
      setSummary('')
      setSymptoms([])
      setSuggestedTreatments([])
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Unable to save encounter')
    }
  }

  return (
    <section className="rounded-[28px] border border-line bg-white p-6">
      <div className="border-b border-line pb-5">
        <p className="text-xs uppercase tracking-[0.2em] text-accent">Encounter creation workflow</p>
        <h2 className="mt-3 text-2xl font-semibold text-ink">Add encounter</h2>
      </div>

      <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <InputField
            label="Encounter title"
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Follow-up visit"
            required
            value={title}
          />
          <InputField
            label="Encounter date and time"
            onChange={(event) => setOccurredAt(event.target.value)}
            type="datetime-local"
            value={occurredAt}
          />
        </div>

        <TextAreaField
          label="Summary"
          onChange={(event) => setSummary(event.target.value)}
          placeholder="Short clinical note for this encounter."
          value={summary}
        />

        <StringListEditor
          buttonLabel="Add symptom"
          error={symptoms.length === 0 && error ? 'At least one symptom is required.' : undefined}
          helperText="Press Enter or click the button to add each symptom."
          label="Symptoms"
          onChange={setSymptoms}
          placeholder="Cough"
          values={symptoms}
        />

        <StringListEditor
          buttonLabel="Add treatment"
          helperText="Optional at creation time. You can edit treatments later."
          label="Suggested treatments"
          onChange={setSuggestedTreatments}
          placeholder="Hydration"
          values={suggestedTreatments}
        />

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        <button
          className="rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={submitting}
          type="submit"
        >
          {submitting ? 'Saving encounter...' : 'Save encounter'}
        </button>
      </form>
    </section>
  )
}

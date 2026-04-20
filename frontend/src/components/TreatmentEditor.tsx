import { useState } from 'react'

import { StringListEditor } from './StringListEditor'

export function TreatmentEditor({
  encounterId,
  initialTreatments,
  onSave,
  submitting,
}: {
  encounterId: string
  initialTreatments: string[]
  onSave: (encounterId: string, suggestedTreatments: string[]) => Promise<void>
  submitting: boolean
}) {
  const [editing, setEditing] = useState(false)
  const [values, setValues] = useState(initialTreatments)
  const [error, setError] = useState('')

  async function handleSave() {
    try {
      setError('')
      await onSave(encounterId, values)
      setEditing(false)
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save treatments')
    }
  }

  function handleCancel() {
    setValues(initialTreatments)
    setError('')
    setEditing(false)
  }

  if (!editing) {
    return (
      <button
        className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
        onClick={() => {
          setValues(initialTreatments)
          setEditing(true)
        }}
        type="button"
      >
        Edit suggested treatments
      </button>
    )
  }

  return (
    <div className="rounded-3xl border border-line bg-white p-4">
      <StringListEditor
        buttonLabel="Add treatment"
        helperText="Click a treatment chip to remove it."
        label="Suggested treatments"
        onChange={setValues}
        placeholder="Rest"
        values={values}
      />
      {error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}
      <div className="mt-4 flex gap-2">
        <button
          className="rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={submitting}
          onClick={handleSave}
          type="button"
        >
          {submitting ? 'Saving...' : 'Save treatments'}
        </button>
        <button
          className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
          onClick={handleCancel}
          type="button"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

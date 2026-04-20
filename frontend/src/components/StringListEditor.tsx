import { useState, type KeyboardEvent } from 'react'

export function StringListEditor({
  label,
  values,
  onChange,
  placeholder,
  buttonLabel,
  helperText,
  error,
}: {
  label: string
  values: string[]
  onChange: (values: string[]) => void
  placeholder: string
  buttonLabel: string
  helperText?: string
  error?: string
}) {
  const [draft, setDraft] = useState('')

  function addValue() {
    const trimmed = draft.trim()

    if (!trimmed || values.includes(trimmed)) {
      setDraft('')
      return
    }

    onChange([...values, trimmed])
    setDraft('')
  }

  function removeValue(value: string) {
    onChange(values.filter((item) => item !== value))
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault()
      addValue()
    }
  }

  return (
    <div>
      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">{label}</span>
        <div className="flex gap-2">
          <input
            className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/10"
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            value={draft}
          />
          <button
            className="rounded-2xl border border-line bg-white px-4 py-3 text-sm font-medium text-ink transition hover:bg-slate-50"
            onClick={addValue}
            type="button"
          >
            {buttonLabel}
          </button>
        </div>
      </label>
      {helperText ? <p className="mt-2 text-xs text-slate-500">{helperText}</p> : null}
      {error ? <p className="mt-2 text-sm text-rose-600">{error}</p> : null}
      <div className="mt-3 flex flex-wrap gap-2">
        {values.length === 0 ? (
          <span className="text-sm text-slate-400">No items added yet.</span>
        ) : (
          values.map((value) => (
            <button
              className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700 transition hover:bg-slate-200"
              key={value}
              onClick={() => removeValue(value)}
              type="button"
            >
              {value} ×
            </button>
          ))
        )}
      </div>
    </div>
  )
}

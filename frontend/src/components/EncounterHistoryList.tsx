import type { ReactNode } from 'react'

import type { EncounterHistoryItem } from '../types/ehr'
import { formatDate } from '../lib/formatters'
import { EmptyState } from './EmptyState'

function DetailPills({
  items,
  emptyLabel,
}: {
  items: string[]
  emptyLabel: string
}) {
  if (items.length === 0) {
    return <span className="text-sm text-slate-400">{emptyLabel}</span>
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span className="rounded-full bg-white px-3 py-1 text-sm text-slate-700" key={item}>
          {item}
        </span>
      ))}
    </div>
  )
}

function aiStatusLabel(status: EncounterHistoryItem['ai']['status']) {
  if (status === 'reviewed') {
    return 'AI reviewed'
  }

  if (status === 'generated') {
    return 'AI generated'
  }

  return 'AI pending'
}

export function EncounterHistoryList({
  encounters,
  title = 'Encounter history',
  description = 'Simple visit summary list',
  renderActions,
}: {
  encounters: EncounterHistoryItem[]
  title?: string
  description?: string
  renderActions?: (encounter: EncounterHistoryItem) => ReactNode
}) {
  if (encounters.length === 0) {
    return (
      <EmptyState
        description="No encounters have been recorded yet."
        title={title}
      />
    )
  }

  return (
    <section className="rounded-[28px] border border-line bg-white p-6">
      <div className="border-b border-line pb-5">
        <p className="text-xs uppercase tracking-[0.2em] text-accent">{description}</p>
        <h2 className="mt-3 text-2xl font-semibold text-ink">{title}</h2>
      </div>

      <div className="mt-5 space-y-4">
        {encounters.map((encounter) => (
          <article
            className="rounded-3xl border border-line bg-slate-50 p-5"
            key={encounter.id}
          >
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                  {formatDate(encounter.occurredAt)}
                </p>
                <h3 className="mt-2 text-lg font-semibold text-ink">{encounter.title}</h3>
                <p className="mt-2 text-sm text-slate-500">{encounter.summary ?? 'No summary recorded.'}</p>
              </div>
              <div className="space-y-2">
                <div className="rounded-2xl bg-white px-4 py-3 text-sm text-slate-500">
                  Doctor: {encounter.doctorName}
                </div>
                <div className="rounded-2xl bg-teal-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-teal-700">
                  {aiStatusLabel(encounter.ai.status)}
                </div>
              </div>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Symptoms</p>
                <div className="mt-2">
                  <DetailPills emptyLabel="No symptoms recorded." items={encounter.symptoms} />
                </div>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
                  Suggested treatments
                </p>
                <div className="mt-2">
                  <DetailPills
                    emptyLabel="No suggested treatments recorded."
                    items={encounter.suggestedTreatments}
                  />
                </div>
              </div>
            </div>

            {renderActions ? <div className="mt-4">{renderActions(encounter)}</div> : null}
          </article>
        ))}
      </div>
    </section>
  )
}

import type { AuditActivityItem } from '../types/ehr'
import { EmptyState } from './EmptyState'
import { formatDate } from '../lib/formatters'

function formatActionLabel(action: string) {
  return action
    .replace(/\./g, ' ')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

export function AuditActivityPanel({
  title,
  description,
  activity,
}: {
  title: string
  description: string
  activity: AuditActivityItem[]
}) {
  if (activity.length === 0) {
    return <EmptyState title={title} description="No recent audit events have been recorded." />
  }

  return (
    <section className="rounded-[28px] border border-line bg-white p-6">
      <div className="border-b border-line pb-5">
        <p className="text-xs uppercase tracking-[0.2em] text-accent">{description}</p>
        <h2 className="mt-3 text-2xl font-semibold text-ink">{title}</h2>
      </div>
      <div className="mt-5 space-y-3">
        {activity.map((event) => (
          <article
            className="rounded-3xl border border-line bg-slate-50 p-5"
            key={event.id}
          >
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                  {formatDate(event.createdAt)}
                </p>
                <h3 className="mt-2 text-base font-semibold text-ink">
                  {formatActionLabel(event.action)}
                </h3>
                <p className="mt-2 text-sm text-slate-500">
                  Actor: {event.actor ? `${event.actor.name} (${event.actor.role})` : 'System'}
                </p>
              </div>
              <div className="rounded-2xl bg-white px-4 py-3 text-xs uppercase tracking-[0.16em] text-slate-500">
                {event.resourceType}
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

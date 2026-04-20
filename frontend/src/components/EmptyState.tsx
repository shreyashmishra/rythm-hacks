export function EmptyState({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <section className="rounded-[28px] border border-dashed border-line bg-white p-6">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Simple EHR</p>
      <h2 className="mt-3 text-2xl font-semibold text-ink">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
    </section>
  )
}

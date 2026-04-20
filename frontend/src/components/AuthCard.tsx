import type { FormEventHandler, PropsWithChildren, ReactNode } from 'react'

export function AuthCard({
  title,
  description,
  footer,
  onSubmit,
  children,
}: PropsWithChildren<{
  title: string
  description: string
  footer: ReactNode
  onSubmit: FormEventHandler<HTMLFormElement>
}>) {
  return (
    <form className="rounded-[28px] border border-line bg-white p-8" onSubmit={onSubmit}>
      <h2 className="text-2xl font-semibold text-ink">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
      <div className="mt-8 space-y-4">{children}</div>
      <div className="mt-8 text-sm text-slate-500">{footer}</div>
    </form>
  )
}

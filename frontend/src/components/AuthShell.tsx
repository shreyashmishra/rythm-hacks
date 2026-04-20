import type { PropsWithChildren } from 'react'

export function AuthShell({
  children,
  eyebrow,
  title,
  subtitle,
}: PropsWithChildren<{
  eyebrow: string
  title: string
  subtitle: string
}>) {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="grid w-full max-w-5xl gap-8 rounded-[32px] border border-white/70 bg-white/80 p-4 shadow-panel backdrop-blur lg:grid-cols-[1.05fr_0.95fr] lg:p-6">
        <section className="rounded-[24px] bg-ink px-6 py-10 text-slate-100 lg:px-10">
          <p className="text-sm uppercase tracking-[0.24em] text-teal-200">{eyebrow}</p>
          <h1 className="mt-6 max-w-sm text-4xl font-semibold leading-tight">{title}</h1>
          <p className="mt-4 max-w-md text-sm leading-6 text-slate-300">{subtitle}</p>
          <div className="mt-12 grid gap-4 text-sm text-slate-200 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="font-medium">Patient access</p>
              <p className="mt-2 text-slate-300">
                Minimal portal shell for onboarding and future health workflows.
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="font-medium">Doctor access</p>
              <p className="mt-2 text-slate-300">
                Role-protected shell prepared for the next product phases.
              </p>
            </div>
          </div>
        </section>
        <section className="flex items-center justify-center rounded-[24px] bg-mist p-4 lg:p-8">
          <div className="w-full max-w-md">{children}</div>
        </section>
      </div>
    </main>
  )
}

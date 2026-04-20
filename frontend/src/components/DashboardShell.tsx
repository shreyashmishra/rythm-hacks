import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function DashboardShell({
  badge,
  title,
  subtitle,
  children,
  actions,
}: {
  badge: string
  title: string
  subtitle: string
  children: ReactNode
  actions?: ReactNode
}) {
  const navigate = useNavigate()
  const { logout, user } = useAuth()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="rounded-[28px] border border-white/70 bg-white/85 px-6 py-5 shadow-panel backdrop-blur">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <span className="inline-flex rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-accent">
                {badge}
              </span>
              <h1 className="mt-4 text-3xl font-semibold text-ink">{title}</h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{subtitle}</p>
            </div>
            <div className="flex items-center gap-3">
              {actions}
              <div className="rounded-2xl border border-line bg-slate-50 px-4 py-3 text-right">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Signed in</p>
                <p className="mt-1 text-sm font-semibold text-ink">{user?.name}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
              <button
                className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
                onClick={handleLogout}
                type="button"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-[28px] border border-white/70 bg-white/85 p-6 shadow-panel backdrop-blur">
            {children}
          </div>
          <aside className="rounded-[28px] border border-white/70 bg-slate-950 p-6 text-slate-100 shadow-panel">
            <p className="text-xs uppercase tracking-[0.2em] text-teal-200">Phase 2</p>
            <h2 className="mt-4 text-xl font-semibold">EHR core structure</h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Profiles, encounters, symptoms, and suggested treatments now provide the
              first simple MedicalAI-style patient record structure.
            </p>
            <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm leading-6 text-slate-300">
              This phase stays intentionally narrow: no AI generation, no multilingual
              features, and no extra workflow complexity yet.
            </div>
            <Link
              className="mt-6 inline-flex rounded-full border border-white/15 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/10"
              to="/"
            >
              Return to role redirect
            </Link>
          </aside>
        </section>
      </div>
    </main>
  )
}

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { AuthCard } from '../components/AuthCard'
import { AuthShell } from '../components/AuthShell'
import { InputField } from '../components/InputField'
import { RoleSelector } from '../components/RoleSelector'
import { useAuth } from '../context/AuthContext'
import type { Role } from '../types/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<Role>('patient')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const user = await login({ email, password, role })
      navigate(user.role === 'doctor' ? '/doctor/dashboard' : '/patient/dashboard')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      eyebrow="Local Auth"
      subtitle="Use the same portal for both roles. The selected role is validated by the backend before the session cookie is issued."
      title="Sign in to the rebuilt Rythm workspace."
    >
      <AuthCard
        description="Enter your credentials and continue into the matching dashboard shell."
        footer={
          <span>
            Need an account?{' '}
            <Link className="font-semibold text-accent" to="/signup">
              Create one
            </Link>
          </span>
        }
        onSubmit={handleSubmit}
        title="Login"
      >
        <RoleSelector onChange={setRole} value={role} />
        <InputField
          autoComplete="email"
          label="Email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          required
          type="email"
          value={email}
        />
        <InputField
          autoComplete="current-password"
          label="Password"
          minLength={8}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Enter your password"
          required
          type="password"
          value={password}
        />
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button
          className="w-full rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={submitting}
          type="submit"
        >
          {submitting ? 'Signing in...' : 'Sign in'}
        </button>
      </AuthCard>
    </AuthShell>
  )
}

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { AuthCard } from '../components/AuthCard'
import { AuthShell } from '../components/AuthShell'
import { InputField } from '../components/InputField'
import { RoleSelector } from '../components/RoleSelector'
import { useAuth } from '../context/AuthContext'
import type { Role } from '../types/auth'

export function SignupPage() {
  const navigate = useNavigate()
  const { signup } = useAuth()
  const [name, setName] = useState('')
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
      const user = await signup({ name, email, password, role })
      navigate(user.role === 'doctor' ? '/doctor/dashboard' : '/patient/dashboard')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Signup failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      eyebrow="Phase 1"
      subtitle="This first pass only handles local identity and role-based navigation. Product workflows come later."
      title="Create a doctor or patient account."
    >
      <AuthCard
        description="New accounts are stored in MySQL through Prisma and passwords are hashed with bcrypt."
        footer={
          <span>
            Already registered?{' '}
            <Link className="font-semibold text-accent" to="/login">
              Sign in
            </Link>
          </span>
        }
        onSubmit={handleSubmit}
        title="Signup"
      >
        <InputField
          autoComplete="name"
          label="Full name"
          onChange={(event) => setName(event.target.value)}
          placeholder="Alex Morgan"
          required
          value={name}
        />
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
          autoComplete="new-password"
          label="Password"
          minLength={8}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="At least 8 characters"
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
          {submitting ? 'Creating account...' : 'Create account'}
        </button>
      </AuthCard>
    </AuthShell>
  )
}

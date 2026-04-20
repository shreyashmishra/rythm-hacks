import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import type { Role } from '../types/auth'

export function ProtectedRoute({
  children,
  allowedRole,
}: PropsWithChildren<{ allowedRole: Role }>) {
  const { loading, user } = useAuth()

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Checking session...
      </main>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== allowedRole) {
    return (
      <Navigate
        replace
        to={user.role === 'doctor' ? '/doctor/dashboard' : '/patient/dashboard'}
      />
    )
  }

  return <>{children}</>
}

import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function PublicOnlyRoute({ children }: PropsWithChildren) {
  const { loading, user } = useAuth()

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Loading...
      </main>
    )
  }

  if (user) {
    return (
      <Navigate
        replace
        to={user.role === 'doctor' ? '/doctor/dashboard' : '/patient/dashboard'}
      />
    )
  }

  return <>{children}</>
}

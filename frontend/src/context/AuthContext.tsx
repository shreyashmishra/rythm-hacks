import {
  createContext,
  useContext,
  useEffect,
  useState,
  type PropsWithChildren,
} from 'react'

import { api } from '../lib/api'
import type { AuthFormValues, User } from '../types/auth'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (values: AuthFormValues) => Promise<User>
  signup: (values: AuthFormValues) => Promise<User>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .me()
      .then((payload) => setUser(payload.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const value: AuthContextValue = {
    user,
    loading,
    login: async (values) => {
      const payload = await api.login(values)
      setUser(payload.user)
      return payload.user
    },
    signup: async (values) => {
      const payload = await api.signup(values)
      setUser(payload.user)
      return payload.user
    },
    logout: async () => {
      await api.logout()
      setUser(null)
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }

  return context
}

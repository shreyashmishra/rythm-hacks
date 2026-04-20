export type Role = 'doctor' | 'patient'

export interface User {
  id: string
  name: string
  email: string
  role: Role
}

export interface AuthPayload {
  user: User
}

export interface AuthFormValues {
  name?: string
  email: string
  password: string
  role: Role
}

import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './components/ProtectedRoute'
import { PublicOnlyRoute } from './components/PublicOnlyRoute'
import { useAuth } from './context/AuthContext'
import { DoctorDashboardPage } from './pages/DoctorDashboardPage'
import { DoctorPatientDetailPage } from './pages/DoctorPatientDetailPage'
import { LoginPage } from './pages/LoginPage'
import { PatientDashboardPage } from './pages/PatientDashboardPage'
import { PatientProfilePage } from './pages/PatientProfilePage'
import { SignupPage } from './pages/SignupPage'

function RoleRedirect() {
  const { user } = useAuth()

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return (
    <Navigate
      replace
      to={user.role === 'doctor' ? '/doctor/dashboard' : '/patient/dashboard'}
    />
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RoleRedirect />} />
        <Route
          path="/login"
          element={
            <PublicOnlyRoute>
              <LoginPage />
            </PublicOnlyRoute>
          }
        />
        <Route
          path="/signup"
          element={
            <PublicOnlyRoute>
              <SignupPage />
            </PublicOnlyRoute>
          }
        />
        <Route
          path="/patient/dashboard"
          element={
            <ProtectedRoute allowedRole="patient">
              <PatientDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/doctor/dashboard"
          element={
            <ProtectedRoute allowedRole="doctor">
              <DoctorDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/doctor/patients/:patientProfileId"
          element={
            <ProtectedRoute allowedRole="doctor">
              <DoctorPatientDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/patient/profile"
          element={
            <ProtectedRoute allowedRole="patient">
              <PatientProfilePage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

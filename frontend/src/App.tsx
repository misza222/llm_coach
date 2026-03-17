import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { CoachPage } from './pages/CoachPage'
import { LoginPage } from './pages/LoginPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<CoachPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

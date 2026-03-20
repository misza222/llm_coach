import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const PROVIDERS = [
  { id: 'google', label: 'Continue with Google', color: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50' },
  { id: 'twitter', label: 'Continue with Twitter', color: 'bg-black text-white hover:bg-gray-900' },
] as const

export function LoginPage() {
  const { anonymousId } = useAuth()
  const navigate = useNavigate()

  const handleLogin = (provider: string) => {
    const params = new URLSearchParams({ anonymous_id: anonymousId })
    window.location.href = `/api/v1/auth/login/${provider}?${params}`
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm space-y-6 rounded-xl bg-white p-8 shadow-lg">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Sign in</h1>
          <p className="mt-2 text-sm text-gray-500">
            Sign in to save your coaching sessions across devices
          </p>
        </div>

        <div className="space-y-3">
          {PROVIDERS.map((p) => (
            <button
              key={p.id}
              onClick={() => handleLogin(p.id)}
              className={`w-full rounded-lg px-4 py-3 text-sm font-medium transition-colors ${p.color}`}
            >
              {p.label}
            </button>
          ))}
        </div>

        <div className="text-center">
          <button
            onClick={() => navigate('/')}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Continue as guest
          </button>
        </div>
      </div>
    </div>
  )
}

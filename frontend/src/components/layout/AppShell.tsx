import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="flex h-screen flex-col bg-white">
      <header className="flex items-center justify-between border-b border-gray-200 px-6 py-3">
        <h1 className="text-lg font-semibold text-gray-900">Life Coach</h1>

        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <>
              <span className="text-sm text-gray-600">
                {user.name ?? user.email ?? 'Signed in'}
              </span>
              <span className="h-2 w-2 rounded-full bg-green-500" title="Signed in" />
              <button
                onClick={logout}
                className="rounded-md border border-gray-300 px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
              >
                Sign out
              </button>
            </>
          ) : (
            <button
              onClick={() => navigate('/login')}
              className="rounded-md bg-indigo-600 px-3 py-1 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
            >
              Sign in
            </button>
          )}
        </div>
      </header>
      <main className="flex flex-1 overflow-hidden">{children}</main>
    </div>
  )
}

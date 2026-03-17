import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { getAuthStatus, logout as apiLogout } from '../api/client'
import type { UserInfo } from '../api/types'

interface AuthState {
  user: UserInfo | null
  isAuthenticated: boolean
  isLoading: boolean
  anonymousId: string
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
}

const ANON_KEY = 'life-coach-user-id'

function getOrCreateAnonymousId(): string {
  const stored = localStorage.getItem(ANON_KEY)
  if (stored) return stored
  const id = crypto.randomUUID()
  localStorage.setItem(ANON_KEY, id)
  return id
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [anonymousId] = useState(getOrCreateAnonymousId)

  const refreshAuth = useCallback(async () => {
    try {
      const status = await getAuthStatus()
      setUser(status.is_authenticated ? status.user : null)
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshAuth()
  }, [refreshAuth])

  const logout = useCallback(async () => {
    await apiLogout()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        anonymousId,
        logout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

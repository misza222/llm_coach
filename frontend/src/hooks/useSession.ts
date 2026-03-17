import { useAuth } from '../contexts/AuthContext'

export function useSession() {
  const { user, isAuthenticated, anonymousId } = useAuth()

  // Authenticated users use their server-side user ID; anonymous users use localStorage UUID
  const userId = isAuthenticated && user ? user.id : anonymousId

  const newSession = () => {
    // Force full reload so all state resets cleanly
    window.location.reload()
  }

  return { userId, newSession }
}

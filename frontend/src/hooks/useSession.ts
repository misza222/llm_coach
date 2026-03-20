import { useCallback, useEffect, useState } from 'react'
import { createNewSession, endSession, listSessions } from '../api/client'
import type { SessionSummary } from '../api/types'
import { useAuth } from '../contexts/AuthContext'

export function useSession() {
  const { user, isAuthenticated, anonymousId } = useAuth()

  const userId = isAuthenticated && user ? user.id : anonymousId

  const [sessionList, setSessionList] = useState<SessionSummary[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)

  // Load session list on mount / userId change; auto-create first session if none exist
  useEffect(() => {
    let cancelled = false
    listSessions(userId)
      .then(async (resp) => {
        if (cancelled) return
        if (resp.sessions.length === 0) {
          // First visit — pre-create a session so the sidebar shows "First session"
          const session = await createNewSession(userId)
          if (cancelled) return
          setSessionList([
            {
              session_id: session.session_id,
              title: session.title,
              status: session.status,
              current_phase: session.current_phase ?? 'INTRODUCTION',
              created_at: session.created_at,
              updated_at: session.created_at,
            },
          ])
          setActiveSessionId(session.session_id)
        } else {
          setSessionList(resp.sessions)
          const active = resp.sessions.find((s) => s.status === 'ACTIVE')
          setActiveSessionId(active?.session_id ?? null)
        }
      })
      .catch(() => {
        // ignore — user just won't have a pre-created session
      })
    return () => {
      cancelled = true
    }
  }, [userId])

  const refreshList = useCallback(async () => {
    try {
      const resp = await listSessions(userId)
      setSessionList(resp.sessions)
    } catch {
      // ignore
    }
  }, [userId])

  const selectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId)
  }, [])

  const startNewSession = useCallback(async () => {
    const session = await createNewSession(userId)
    setActiveSessionId(session.session_id)
    await refreshList()
    return session
  }, [userId, refreshList])

  const endCurrentSession = useCallback(async () => {
    if (!activeSessionId) return
    await endSession(userId, activeSessionId)
    await refreshList()
  }, [userId, activeSessionId, refreshList])

  return {
    userId,
    sessionList,
    activeSessionId,
    selectSession,
    startNewSession,
    endCurrentSession,
    refreshList,
  }
}

import { useCallback, useEffect, useState } from 'react'
import { ApiError, getSession, resetSession, sendMessage } from '../api/client'
import type { ChatMessage } from '../api/types'

interface SessionMeta {
  phase: string
  detectedEmotions: string[]
  mainGoal: string | null
  userName: string | null
}

const EMPTY_META: SessionMeta = {
  phase: 'INTRODUCTION',
  detectedEmotions: [],
  mainGoal: null,
  userName: null,
}

export function useChat(userId: string) {
  const [history, setHistory] = useState<ChatMessage[]>([])
  const [meta, setMeta] = useState<SessionMeta>(EMPTY_META)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loginRequired, setLoginRequired] = useState(false)
  const [remainingMessages, setRemainingMessages] = useState<number | null>(null)

  // Load existing session on mount
  useEffect(() => {
    let cancelled = false
    getSession(userId)
      .then((session) => {
        if (cancelled) return
        setHistory(session.history)
        setMeta({
          phase: session.current_phase ?? 'INTRODUCTION',
          detectedEmotions: session.detected_emotions,
          mainGoal: session.main_goal,
          userName: session.user_name,
        })
      })
      .catch(() => {
        // 404 = no session yet, that's fine
      })
    return () => {
      cancelled = true
    }
  }, [userId])

  const send = useCallback(
    async (message: string) => {
      if (!message.trim() || isSending || loginRequired) return
      setError(null)

      // Optimistic: show user message immediately
      setHistory((prev) => [...prev, { role: 'user', content: message }])
      setIsSending(true)

      try {
        const response = await sendMessage({ user_id: userId, message })
        // Server history is source of truth
        setHistory(response.history)
        setMeta({
          phase: response.phase,
          detectedEmotions: response.detected_emotions,
          mainGoal: meta.mainGoal,
          userName: meta.userName,
        })
        setRemainingMessages(response.remaining_messages)
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoginRequired(true)
          setHistory((prev) => prev.slice(0, -1))
        } else {
          const msg = err instanceof Error ? err.message : 'Something went wrong'
          setError(msg)
          setHistory((prev) => prev.slice(0, -1))
        }
      } finally {
        setIsSending(false)
      }
    },
    [userId, isSending, loginRequired, meta.mainGoal, meta.userName],
  )

  const reset = useCallback(async () => {
    await resetSession(userId)
    setHistory([])
    setMeta(EMPTY_META)
    setError(null)
    setLoginRequired(false)
    setRemainingMessages(null)
  }, [userId])

  return { history, meta, isSending, error, send, reset, loginRequired, remainingMessages }
}

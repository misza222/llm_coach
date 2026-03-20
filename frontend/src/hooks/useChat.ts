import { useCallback, useEffect, useState } from 'react'
import { ApiError, getSessionById, sendMessage } from '../api/client'
import type { ChatMessage } from '../api/types'

interface SessionMeta {
  phase: string
  status: string
  detectedEmotions: string[]
  mainGoal: string | null
  userName: string | null
  title: string | null
}

const EMPTY_META: SessionMeta = {
  phase: 'INTRODUCTION',
  status: 'ACTIVE',
  detectedEmotions: [],
  mainGoal: null,
  userName: null,
  title: null,
}

export function useChat(userId: string, sessionId: string | null) {
  const [history, setHistory] = useState<ChatMessage[]>([])
  const [meta, setMeta] = useState<SessionMeta>(EMPTY_META)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loginRequired, setLoginRequired] = useState(false)
  const [remainingMessages, setRemainingMessages] = useState<number | null>(null)
  const [isClosing, setIsClosing] = useState(false)
  // Track the session_id returned by the server (for auto-created sessions)
  const [resolvedSessionId, setResolvedSessionId] = useState<string | null>(sessionId)

  // Load existing session when sessionId changes
  useEffect(() => {
    if (!sessionId) {
      setHistory([])
      setMeta(EMPTY_META)
      setIsClosing(false)
      setResolvedSessionId(null)
      return
    }

    let cancelled = false
    getSessionById(userId, sessionId)
      .then((session) => {
        if (cancelled) return
        setHistory(session.history)
        setMeta({
          phase: session.current_phase ?? 'INTRODUCTION',
          status: session.status,
          detectedEmotions: session.detected_emotions,
          mainGoal: session.main_goal,
          userName: session.user_name,
          title: session.title,
        })
        setResolvedSessionId(session.session_id)
        setIsClosing(false)
      })
      .catch(() => {
        // 404 = no session yet
      })
    return () => {
      cancelled = true
    }
  }, [userId, sessionId])

  const isCompleted = meta.status === 'COMPLETED'

  const send = useCallback(
    async (message: string) => {
      if (!message.trim() || isSending || loginRequired || isCompleted) return
      setError(null)

      // Optimistic: show user message immediately
      setHistory((prev) => [...prev, { role: 'user', content: message }])
      setIsSending(true)

      try {
        const response = await sendMessage({
          user_id: userId,
          message,
          session_id: resolvedSessionId,
        })
        // Server history is source of truth
        setHistory(response.history)
        setMeta({
          phase: response.phase,
          status: response.status,
          detectedEmotions: response.detected_emotions,
          mainGoal: meta.mainGoal,
          userName: meta.userName,
          title: meta.title,
        })
        setRemainingMessages(response.remaining_messages)
        setIsClosing(response.is_closing)
        setResolvedSessionId(response.session_id)
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoginRequired(true)
          setHistory((prev) => prev.slice(0, -1))
        } else if (err instanceof ApiError && err.status === 409) {
          setMeta((prev) => ({ ...prev, status: 'COMPLETED' }))
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
    [userId, resolvedSessionId, isSending, loginRequired, isCompleted, meta],
  )

  return {
    history,
    meta,
    isSending,
    error,
    send,
    loginRequired,
    remainingMessages,
    isClosing,
    isCompleted,
    resolvedSessionId,
  }
}

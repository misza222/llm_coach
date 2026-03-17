import { useState } from 'react'

const STORAGE_KEY = 'life-coach-user-id'

function getOrCreateUserId(): string {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) return stored
  const id = crypto.randomUUID()
  localStorage.setItem(STORAGE_KEY, id)
  return id
}

export function useSession() {
  const [userId] = useState(getOrCreateUserId)

  const newSession = () => {
    const id = crypto.randomUUID()
    localStorage.setItem(STORAGE_KEY, id)
    // Force full reload so all state resets cleanly
    window.location.reload()
  }

  return { userId, newSession }
}

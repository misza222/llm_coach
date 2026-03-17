import type { AuthStatusResponse, ChatRequest, ChatResponse, SessionResponse } from './types'

class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...options,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(response.status, body.detail ?? `Request failed: ${response.status}`)
  }
  return response.json()
}

export async function sendMessage(payload: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/api/v1/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getSession(userId: string): Promise<SessionResponse> {
  return request<SessionResponse>(`/api/v1/sessions/${encodeURIComponent(userId)}`)
}

export async function resetSession(userId: string): Promise<void> {
  await request(`/api/v1/sessions/${encodeURIComponent(userId)}/reset`, {
    method: 'POST',
  })
}

export async function getAuthStatus(): Promise<AuthStatusResponse> {
  return request<AuthStatusResponse>('/api/v1/auth/me')
}

export async function logout(): Promise<void> {
  await request('/api/v1/auth/logout', { method: 'POST' })
}

export { ApiError }

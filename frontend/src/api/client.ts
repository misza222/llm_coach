import type {
  AuthStatusResponse,
  ChatRequest,
  ChatResponse,
  SessionListResponse,
  SessionResponse,
} from './types'

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

export async function listSessions(userId: string): Promise<SessionListResponse> {
  return request<SessionListResponse>(`/api/v1/sessions/${encodeURIComponent(userId)}`)
}

export async function getSessionById(
  userId: string,
  sessionId: string,
): Promise<SessionResponse> {
  return request<SessionResponse>(
    `/api/v1/sessions/${encodeURIComponent(userId)}/${encodeURIComponent(sessionId)}`,
  )
}

export async function createNewSession(userId: string): Promise<SessionResponse> {
  return request<SessionResponse>(`/api/v1/sessions/${encodeURIComponent(userId)}/new`, {
    method: 'POST',
  })
}

export async function endSession(userId: string, sessionId: string): Promise<void> {
  await request(
    `/api/v1/sessions/${encodeURIComponent(userId)}/${encodeURIComponent(sessionId)}/end`,
    { method: 'POST' },
  )
}

export async function deleteSession(userId: string, sessionId: string): Promise<void> {
  await request(
    `/api/v1/sessions/${encodeURIComponent(userId)}/${encodeURIComponent(sessionId)}`,
    { method: 'DELETE' },
  )
}

export async function exportSession(userId: string, sessionId: string): Promise<void> {
  const url = `/api/v1/sessions/${encodeURIComponent(userId)}/${encodeURIComponent(sessionId)}/export`
  window.open(url, '_blank')
}

export async function getAuthStatus(): Promise<AuthStatusResponse> {
  return request<AuthStatusResponse>('/api/v1/auth/me')
}

export async function logout(): Promise<void> {
  await request('/api/v1/auth/logout', { method: 'POST' })
}

export { ApiError }

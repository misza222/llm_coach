export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  user_id: string
  message: string
  session_id?: string | null
}

export interface ChatResponse {
  reply: string
  session_id: string
  status: string
  phase: string
  detected_emotions: string[]
  history: ChatMessage[]
  is_anonymous: boolean
  remaining_messages: number | null
  is_closing: boolean
}

export interface SessionSummary {
  session_id: string
  title: string | null
  status: string
  current_phase: string
  created_at: string
  updated_at: string
}

export interface SessionListResponse {
  sessions: SessionSummary[]
}

export interface SessionResponse {
  session_id: string
  user_id: string
  user_name: string | null
  current_phase: string | null
  main_goal: string | null
  status: string
  title: string | null
  detected_emotions: string[]
  history: ChatMessage[]
  created_at: string
}

export interface UserInfo {
  id: string
  email: string | null
  name: string | null
  provider: string | null
}

export interface AuthStatusResponse {
  is_authenticated: boolean
  user: UserInfo | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  user_id: string
  message: string
}

export interface ChatResponse {
  reply: string
  phase: string
  detected_emotions: string[]
  history: ChatMessage[]
  is_anonymous: boolean
  remaining_messages: number | null
}

export interface SessionResponse {
  user_id: string
  user_name: string | null
  current_phase: string | null
  main_goal: string | null
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

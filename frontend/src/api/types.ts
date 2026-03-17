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

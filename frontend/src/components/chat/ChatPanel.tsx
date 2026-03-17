import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../../api/types'
import { LoadingSpinner } from '../common/LoadingSpinner'
import { ChatInput } from './ChatInput'
import { MessageBubble } from './MessageBubble'

interface ChatPanelProps {
  history: ChatMessage[]
  isSending: boolean
  onSend: (message: string) => void
}

export function ChatPanel({ history, isSending, onSend }: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, isSending])

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {history.length === 0 && (
          <p className="text-center text-gray-400 mt-20 text-sm">
            Start a conversation with your coach.
          </p>
        )}
        {history.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        {isSending && (
          <div className="flex justify-start">
            <LoadingSpinner />
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={onSend} disabled={isSending} />
    </div>
  )
}

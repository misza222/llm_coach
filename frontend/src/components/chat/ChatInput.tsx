import { useState, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState('')

  const handleSend = () => {
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex gap-2 border-t border-gray-200 bg-white p-4">
      <textarea
        data-testid="chat-input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message..."
        rows={2}
        disabled={disabled}
        className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm
                   focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none
                   disabled:bg-gray-50 disabled:text-gray-400"
      />
      <button
        data-testid="send-btn"
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        className="self-end rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white
                   hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                   transition-colors"
      >
        Send
      </button>
    </div>
  )
}

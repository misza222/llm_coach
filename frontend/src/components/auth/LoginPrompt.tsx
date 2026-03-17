import { useNavigate } from 'react-router-dom'

export function LoginPrompt() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col items-center gap-3 border-t border-gray-200 bg-amber-50 p-4">
      <p className="text-sm text-amber-800">
        You've reached the free message limit. Sign in to continue chatting.
      </p>
      <button
        onClick={() => navigate('/login')}
        className="rounded-lg bg-indigo-600 px-6 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
      >
        Sign in
      </button>
    </div>
  )
}

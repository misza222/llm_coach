import type { SessionSummary } from '../../api/types'

interface SidebarProps {
  phase: string
  detectedEmotions: string[]
  mainGoal: string | null
  sessionList: SessionSummary[]
  activeSessionId: string | null
  isCompleted: boolean
  onNewSession: () => void
  onSelectSession: (sessionId: string) => void
  onEndSession: () => void
  remainingMessages: number | null
  isAuthenticated: boolean
}

function formatPhase(phase: string): string {
  return phase
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ')
}

function formatDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function Sidebar({
  phase,
  detectedEmotions,
  mainGoal,
  sessionList,
  activeSessionId,
  isCompleted,
  onNewSession,
  onSelectSession,
  onEndSession,
  remainingMessages,
  isAuthenticated,
}: SidebarProps) {
  return (
    <aside className="flex w-64 flex-col border-l border-gray-200 bg-gray-50 p-4">
      {/* Guest message count */}
      {!isAuthenticated && remainingMessages !== null && (
        <div className="mb-4 border-b border-gray-200 pb-4">
          <p className="text-xs text-amber-600">
            {remainingMessages} free message{remainingMessages !== 1 ? 's' : ''} left
          </p>
        </div>
      )}

      {/* Session list */}
      <h2 className="mb-2 text-sm font-semibold text-gray-500 uppercase tracking-wide">
        Sessions
      </h2>
      <div className="mb-4 max-h-48 overflow-y-auto space-y-1">
        {sessionList.map((s) => (
          <button
            key={s.session_id}
            onClick={() => onSelectSession(s.session_id)}
            className={`w-full text-left rounded-lg px-3 py-2 text-xs transition-colors ${
              s.session_id === activeSessionId
                ? 'bg-indigo-100 text-indigo-800 font-medium'
                : s.status === 'COMPLETED'
                  ? 'text-gray-400 hover:bg-gray-100'
                  : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="truncate">{s.title || 'Untitled'}</span>
              {s.status === 'COMPLETED' && (
                <span className="ml-1 shrink-0 text-[10px] text-gray-400">done</span>
              )}
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5">{formatDate(s.updated_at)}</div>
          </button>
        ))}
        {sessionList.length === 0 && (
          <p className="px-3 py-2 text-xs text-gray-400 italic">No sessions yet</p>
        )}
      </div>

      <button
        onClick={onNewSession}
        className="mb-4 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium
                   text-gray-700 hover:bg-gray-100 transition-colors"
      >
        New Session
      </button>

      {/* Current session info */}
      <h2 className="mb-4 text-sm font-semibold text-gray-500 uppercase tracking-wide">
        Session Info
      </h2>

      {/* Phase */}
      <div className="mb-4">
        <p className="text-xs font-medium text-gray-500">Phase</p>
        <span className="mt-1 inline-block rounded-full bg-indigo-100 px-3 py-0.5 text-xs font-medium text-indigo-700">
          {formatPhase(phase)}
        </span>
      </div>

      {/* Goal */}
      {mainGoal && (
        <div className="mb-4">
          <p className="text-xs font-medium text-gray-500">Goal</p>
          <p className="mt-1 text-sm text-gray-700">{mainGoal}</p>
        </div>
      )}

      {/* Emotions */}
      {detectedEmotions.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-medium text-gray-500">Emotions</p>
          <div className="mt-1 flex flex-wrap gap-1">
            {detectedEmotions.map((emotion) => (
              <span
                key={emotion}
                className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800"
              >
                {emotion}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* End session button */}
      {!isCompleted && activeSessionId && (
        <div className="mt-auto">
          <button
            onClick={onEndSession}
            className="w-full rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-medium
                       text-red-600 hover:bg-red-50 transition-colors"
          >
            End Session
          </button>
        </div>
      )}
    </aside>
  )
}

interface SidebarProps {
  phase: string
  detectedEmotions: string[]
  mainGoal: string | null
  onNewSession: () => void
  remainingMessages: number | null
  isAuthenticated: boolean
}

function formatPhase(phase: string): string {
  return phase
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ')
}

export function Sidebar({
  phase,
  detectedEmotions,
  mainGoal,
  onNewSession,
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

      <div className="mt-auto">
        <button
          onClick={onNewSession}
          className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium
                     text-gray-700 hover:bg-gray-100 transition-colors"
        >
          New Session
        </button>
      </div>
    </aside>
  )
}

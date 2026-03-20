import { LoginPrompt } from '../components/auth/LoginPrompt'
import { ChatPanel } from '../components/chat/ChatPanel'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { AppShell } from '../components/layout/AppShell'
import { Sidebar } from '../components/sidebar/Sidebar'
import { useAuth } from '../contexts/AuthContext'
import { useChat } from '../hooks/useChat'
import { useSession } from '../hooks/useSession'

export function CoachPage() {
  const {
    userId,
    sessionList,
    activeSessionId,
    selectSession,
    startNewSession,
    endCurrentSession,
    refreshList,
  } = useSession()
  const { isAuthenticated } = useAuth()
  const {
    history,
    meta,
    isSending,
    error,
    send,
    reload: reloadSession,
    loginRequired,
    remainingMessages,
    isClosing,
    isCompleted,
  } = useChat(userId, activeSessionId)

  const handleSend = async (message: string) => {
    await send(message)
    // Refresh the session list so sidebar titles update immediately after chatting
    await refreshList()
  }

  const handleNewSession = async () => {
    await startNewSession()
  }

  const handleEndSession = async () => {
    await endCurrentSession()
    reloadSession()
    await refreshList()
  }

  const handleClosingConfirm = async () => {
    await endCurrentSession()
    reloadSession()
    await refreshList()
  }

  return (
    <AppShell>
      <div className="flex flex-1 flex-col overflow-hidden">
        {error && <ErrorBanner message={error} />}

        {/* Completed session banner */}
        {isCompleted && (
          <div
            data-testid="session-completed-banner"
            className="bg-gray-100 border-b border-gray-200 px-4 py-3 text-center text-sm text-gray-500"
          >
            This session has ended.{' '}
            <button
              data-testid="start-new-session-link"
              onClick={handleNewSession}
              className="text-indigo-600 hover:text-indigo-800 font-medium underline"
            >
              Start a new session
            </button>
          </div>
        )}

        {/* Closing prompt */}
        {isClosing && !isCompleted && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 text-center text-sm text-amber-800">
            Your coach has wrapped up this session.{' '}
            <button
              onClick={handleClosingConfirm}
              className="font-medium underline hover:text-amber-900"
            >
              End session
            </button>
            {' or keep chatting.'}
          </div>
        )}

        {loginRequired ? (
          <>
            <ChatPanel history={history} isSending={false} onSend={() => {}} />
            <LoginPrompt />
          </>
        ) : (
          <ChatPanel
            history={history}
            isSending={isSending}
            onSend={isCompleted ? () => {} : handleSend}
          />
        )}
      </div>
      <div className="hidden md:flex">
        <Sidebar
          phase={meta.phase}
          detectedEmotions={meta.detectedEmotions}
          mainGoal={meta.mainGoal}
          sessionList={sessionList}
          activeSessionId={activeSessionId}
          isCompleted={isCompleted}
          onNewSession={handleNewSession}
          onSelectSession={selectSession}
          onEndSession={handleEndSession}
          remainingMessages={remainingMessages}
          isAuthenticated={isAuthenticated}
        />
      </div>
    </AppShell>
  )
}

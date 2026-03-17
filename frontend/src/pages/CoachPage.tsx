import { ChatPanel } from '../components/chat/ChatPanel'
import { ErrorBanner } from '../components/common/ErrorBanner'
import { AppShell } from '../components/layout/AppShell'
import { Sidebar } from '../components/sidebar/Sidebar'
import { useChat } from '../hooks/useChat'
import { useSession } from '../hooks/useSession'

export function CoachPage() {
  const { userId, newSession } = useSession()
  const { history, meta, isSending, error, send, reset } = useChat(userId)

  const handleNewSession = async () => {
    await reset()
    newSession()
  }

  return (
    <AppShell>
      <div className="flex flex-1 flex-col overflow-hidden">
        {error && <ErrorBanner message={error} />}
        <ChatPanel history={history} isSending={isSending} onSend={send} />
      </div>
      <div className="hidden md:flex">
        <Sidebar
          phase={meta.phase}
          detectedEmotions={meta.detectedEmotions}
          mainGoal={meta.mainGoal}
          onNewSession={handleNewSession}
        />
      </div>
    </AppShell>
  )
}

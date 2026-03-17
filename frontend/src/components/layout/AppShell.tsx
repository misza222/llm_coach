import type { ReactNode } from 'react'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex h-screen flex-col bg-white">
      <header className="flex items-center border-b border-gray-200 px-6 py-3">
        <h1 className="text-lg font-semibold text-gray-900">Life Coach</h1>
      </header>
      <main className="flex flex-1 overflow-hidden">{children}</main>
    </div>
  )
}

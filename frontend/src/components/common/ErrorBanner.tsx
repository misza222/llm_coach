interface ErrorBannerProps {
  message: string
  onDismiss?: () => void
}

export function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  return (
    <div className="mx-4 mb-2 flex items-center justify-between rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">
      <span>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="ml-2 font-medium hover:text-red-900">
          Dismiss
        </button>
      )}
    </div>
  )
}

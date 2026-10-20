import { AlertTriangle, RefreshCw, X } from 'lucide-react'

type Props = { message: string; onRetry?: () => void; onDismiss: () => void }

export default function ErrorBanner({ message, onRetry, onDismiss }: Props) {
  return (
    <div className="error-banner" role="alert">
      <AlertTriangle size={20} aria-hidden="true" />
      <div className="error-text">
        <strong>Something went wrong</strong>
        <p>We couldn't load your data. Please try again in a moment.</p>
        <small>{message}</small>
      </div>
      <div className="error-actions">
        {onRetry && (
          <button type="button" onClick={onRetry}>
            <RefreshCw size={14} aria-hidden="true" />
            Try again
          </button>
        )}
        <button type="button" className="icon-btn" onClick={onDismiss} aria-label="Dismiss">
          <X size={16} aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}
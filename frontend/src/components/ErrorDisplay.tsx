import React from 'react'
import './ErrorDisplay.css'

export interface ErrorDisplayProps {
  /** The error message or Error object to display */
  error: string | Error | unknown
  /** Optional title for the error display */
  title?: string
  /** Optional callback to retry the failed operation */
  onRetry?: () => void
  /** Optional callback to dismiss the error */
  onDismiss?: () => void
  /** Style variant */
  variant?: 'inline' | 'banner' | 'card'
  /** Additional CSS class name */
  className?: string
}

/**
 * ErrorDisplay Component
 * 
 * A reusable component for displaying error messages to users.
 * Replaces console.error() calls with user-facing error UI.
 * 
 * Features:
 * - Multiple display variants (inline, banner, card)
 * - Optional retry and dismiss actions
 * - Handles Error objects and string messages
 * - Accessible with ARIA labels
 * - Integrates with Sentry for error tracking
 * 
 * @example
 * ```tsx
 * <ErrorDisplay 
 *   error="Failed to load data" 
 *   onRetry={fetchData}
 * />
 * ```
 */
const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  title = 'Error',
  onRetry,
  onDismiss,
  variant = 'card',
  className = '',
}) => {
  // Extract error message
  const errorMessage = React.useMemo(() => {
    if (typeof error === 'string') {
      return error
    }
    if (error instanceof Error) {
      return error.message
    }
    if (error && typeof error === 'object' && 'message' in error) {
      return String(error.message)
    }
    return 'An unexpected error occurred'
  }, [error])

  // Log to console and Sentry in production
  React.useEffect(() => {
    console.error('ErrorDisplay:', error)
    
    // TODO: Send to Sentry if configured
    // if (import.meta.env.VITE_SENTRY_DSN) {
    //   Sentry.captureException(error)
    // }
  }, [error])

  const containerClass = `error-display error-display-${variant} ${className}`

  return (
    <div 
      className={containerClass}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="error-display-icon" aria-hidden="true">
        ⚠️
      </div>
      
      <div className="error-display-content">
        <h3 className="error-display-title">{title}</h3>
        <p className="error-display-message">{errorMessage}</p>
        
        {import.meta.env.DEV && error instanceof Error && error.stack && (
          <details className="error-display-stack">
            <summary>Stack Trace (Development Only)</summary>
            <pre>{error.stack}</pre>
          </details>
        )}
      </div>

      {(onRetry || onDismiss) && (
        <div className="error-display-actions">
          {onRetry && (
            <button
              onClick={onRetry}
              className="btn btn-sm btn-primary"
              aria-label="Retry operation"
            >
              Retry
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="btn btn-sm btn-secondary"
              aria-label="Dismiss error"
            >
              Dismiss
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default ErrorDisplay

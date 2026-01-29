import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { calendarApi } from '../api/calendar'
import './CalendarOAuthCallback.css'

const CalendarOAuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [message, setMessage] = useState('Processing OAuth callback...')

  // Normalize API error payloads without falling back to `any`.
  const resolveOAuthError = (error: unknown) => {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as { response?: { data?: { error?: string } } }).response
      return response?.data?.error
    }
    if (error instanceof Error) {
      return error.message
    }
    return undefined
  }

  useEffect(() => {
    let timeoutId: NodeJS.Timeout

    const handleCallback = async () => {
      const code = searchParams.get('code')
      const state = searchParams.get('state')
      const error = searchParams.get('error')

      if (error) {
        setStatus('error')
        setMessage(`OAuth error: ${error}`)
        timeoutId = setTimeout(() => navigate('/calendar-sync'), 3000)
        return
      }

      if (!code || !state) {
        setStatus('error')
        setMessage('Missing authorization code or state')
        timeoutId = setTimeout(() => navigate('/calendar-sync'), 3000)
        return
      }

      try {
        const result = await calendarApi.handleOAuthCallback(code, state)
        setStatus('success')
        setMessage(result.message || 'Calendar connected successfully!')
        timeoutId = setTimeout(() => navigate('/calendar-sync'), 2000)
      } catch (error) {
        setStatus('error')
        setMessage(
          resolveOAuthError(error) || 'Failed to connect calendar. Please try again.'
        )
        timeoutId = setTimeout(() => navigate('/calendar-sync'), 3000)
      }
    }

    handleCallback()

    // Cleanup timeout on unmount
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
    }
  }, [searchParams, navigate])

  return (
    <div className="oauth-callback-page">
      <div className="callback-container">
        {status === 'processing' && (
          <div className="callback-processing">
            <div className="spinner"></div>
            <h2>Connecting Calendar...</h2>
            <p>{message}</p>
          </div>
        )}

        {status === 'success' && (
          <div className="callback-success">
            <div className="success-icon">✓</div>
            <h2>Success!</h2>
            <p>{message}</p>
            <p className="redirect-message">Redirecting to calendar settings...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="callback-error">
            <div className="error-icon">✗</div>
            <h2>Connection Failed</h2>
            <p>{message}</p>
            <p className="redirect-message">Redirecting back...</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default CalendarOAuthCallback

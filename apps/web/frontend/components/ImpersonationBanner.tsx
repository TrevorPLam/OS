/**
 * Impersonation Mode Banner Component
 *
 * TIER 0.6: Break-glass impersonation mode indicator
 *
 * Displays a prominent warning banner when a platform operator is in
 * break-glass impersonation mode. This ensures visibility and accountability
 * for all content access during break-glass sessions.
 *
 * Features:
 * - Prominent visual warning (red/orange banner)
 * - Session details (impersonated user, reason, time remaining)
 * - Countdown timer until session expires
 * - Ability to end session early
 * - Persistent across all pages during active session
 */
import React, { useEffect, useState } from 'react';
import './ImpersonationBanner.css';

interface BreakGlassSession {
  id: number;
  impersonated_user: string | null;
  operator: string;
  reason: string;
  activated_at: string;
  expires_at: string;
  time_remaining_seconds: number;
}

interface BreakGlassStatus {
  is_impersonating: boolean;
  session: BreakGlassSession | null;
}

export const ImpersonationBanner: React.FC = () => {
  const [status, setStatus] = useState<BreakGlassStatus | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [isEnding, setIsEnding] = useState(false);

  // Fetch break-glass status on mount and every 30 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/firm/break-glass/status/');
        if (response.ok) {
          const data: BreakGlassStatus = await response.json();
          setStatus(data);
          if (data.session) {
            setTimeRemaining(data.session.time_remaining_seconds);
          }
        }
      } catch (error) {
        console.error('Failed to fetch break-glass status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Poll every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Countdown timer
  useEffect(() => {
    if (!status?.is_impersonating || timeRemaining <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          // Session expired, refresh status
          window.location.reload();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [status?.is_impersonating, timeRemaining]);

  const handleEndSession = async () => {
    if (!status?.session) return;

    const reason = prompt('Please provide a reason for ending this break-glass session:');
    if (!reason) return;

    setIsEnding(true);

    try {
      const response = await fetch('/api/firm/break-glass/end-session/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason }),
      });

      if (response.ok) {
        // Session ended successfully, reload page
        window.location.reload();
      } else {
        const error = await response.json();
        alert(`Failed to end session: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to end break-glass session:', error);
      alert('Failed to end session. Please try again.');
    } finally {
      setIsEnding(false);
    }
  };

  const formatTimeRemaining = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  // Don't render if not impersonating
  if (!status?.is_impersonating || !status.session) {
    return null;
  }

  const { session } = status;
  const isExpiringSoon = timeRemaining < 300; // Less than 5 minutes

  return (
    <div className={`impersonation-banner ${isExpiringSoon ? 'expiring-soon' : ''}`}>
      <div className="impersonation-banner-content">
        <div className="impersonation-banner-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <div className="impersonation-banner-details">
          <div className="impersonation-banner-title">
            ⚠️ BREAK-GLASS MODE ACTIVE
          </div>
          <div className="impersonation-banner-info">
            {session.impersonated_user && (
              <span className="impersonation-info-item">
                <strong>Impersonating:</strong> {session.impersonated_user}
              </span>
            )}
            <span className="impersonation-info-item">
              <strong>Reason:</strong> {session.reason}
            </span>
            <span className="impersonation-info-item">
              <strong>Operator:</strong> {session.operator}
            </span>
            <span className={`impersonation-info-item ${isExpiringSoon ? 'warning' : ''}`}>
              <strong>Time Remaining:</strong> {formatTimeRemaining(timeRemaining)}
            </span>
          </div>
        </div>

        <div className="impersonation-banner-actions">
          <button
            onClick={handleEndSession}
            disabled={isEnding}
            className="end-session-button"
          >
            {isEnding ? 'Ending...' : 'End Session'}
          </button>
        </div>
      </div>

      <div className="impersonation-banner-notice">
        All actions during this session are audited and logged.
      </div>
    </div>
  );
};

export default ImpersonationBanner;

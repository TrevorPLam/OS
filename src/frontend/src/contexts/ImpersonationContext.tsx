import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'

interface ImpersonationState {
  active: boolean
  impersonatedUser?: string
  reason?: string
  expiresAt?: string
}

const defaultState: ImpersonationState = { active: false }

const ImpersonationContext = createContext<ImpersonationState>(defaultState)

export const useImpersonation = () => useContext(ImpersonationContext)

interface Props {
  children: ReactNode
}

export const ImpersonationProvider: React.FC<Props> = ({ children }) => {
  const [state, setState] = useState<ImpersonationState>(() => {
    const stored = localStorage.getItem('impersonation_state')
    return stored ? JSON.parse(stored) : defaultState
  })

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail

      if (detail?.active) {
        const nextState: ImpersonationState = {
          active: true,
          impersonatedUser: detail.impersonated_user || detail.impersonatedUser,
          reason: detail.reason,
          expiresAt: detail.expires_at || detail.expiresAt,
        }
        setState(nextState)
        localStorage.setItem('impersonation_state', JSON.stringify(nextState))
      } else {
        setState(defaultState)
        localStorage.removeItem('impersonation_state')
      }
    }

    window.addEventListener('impersonation-status', handler as EventListener)

    return () => window.removeEventListener('impersonation-status', handler as EventListener)
  }, [])

  return (
    <ImpersonationContext.Provider value={state}>
      {children}
    </ImpersonationContext.Provider>
  )
}

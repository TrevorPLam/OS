import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AuthProvider, useAuth } from '../AuthContext'
import { User } from '../../api/auth'

const loginMutation = {
  mutateAsync: vi.fn(),
}
const registerMutation = {
  mutateAsync: vi.fn(),
}
const logoutMutation = {
  mutateAsync: vi.fn(),
}

let profileData: User | undefined
let profileLoading = false

vi.mock('../../api/auth', () => ({
  useProfile: () => ({ data: profileData, isLoading: profileLoading }),
  useLogin: () => loginMutation,
  useRegister: () => registerMutation,
  useLogout: () => logoutMutation,
}))

const renderWithProvider = (ui: React.ReactNode) => render(<AuthProvider>{ui}</AuthProvider>)

const mockUser = {
  id: 1,
  username: 'demo',
  email: 'demo@example.com',
  first_name: 'Demo',
  last_name: 'User',
  date_joined: '2024-01-01',
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
    localStorage.clear()
    profileData = undefined
    profileLoading = false
  })

  it('hydrates user from profile endpoint without using localStorage', async () => {
    profileData = mockUser
    const setItemSpy = vi.spyOn(window.localStorage, 'setItem')
    const getItemSpy = vi.spyOn(window.localStorage, 'getItem')

    const ProfileConsumer = () => {
      const { user, loading } = useAuth()
      if (loading) return <div>loading</div>
      return <div>{user?.email ?? 'anon'}</div>
    }

    renderWithProvider(<ProfileConsumer />)

    await waitFor(() => expect(screen.getByText(mockUser.email)).toBeInTheDocument())
    expect(setItemSpy).not.toHaveBeenCalled()
    expect(getItemSpy).not.toHaveBeenCalled()
  })

  it('updates user on login without writing tokens to localStorage', async () => {
    profileData = undefined
    loginMutation.mutateAsync.mockResolvedValue({ user: mockUser, message: 'Login successful' })
    const setItemSpy = vi.spyOn(window.localStorage, 'setItem')

    const LoginConsumer = () => {
      const { user, login, loading } = useAuth()

      if (loading) return <div>loading</div>

      return (
        <div>
          <div data-testid="user-email">{user?.email ?? 'none'}</div>
          <button onClick={() => login({ username: 'demo', password: 'pass' })}>login</button>
        </div>
      )
    }

    renderWithProvider(<LoginConsumer />)

    await waitFor(() => expect(screen.getByTestId('user-email')).toHaveTextContent('none'))

    await userEvent.click(screen.getByText('login'))

    await waitFor(() => expect(screen.getByTestId('user-email')).toHaveTextContent(mockUser.email))
    expect(loginMutation.mutateAsync).toHaveBeenCalledWith({ username: 'demo', password: 'pass' })
    expect(setItemSpy).not.toHaveBeenCalled()
  })

  it('clears user state on logout while relying solely on cookies', async () => {
    profileData = mockUser
    logoutMutation.mutateAsync.mockResolvedValue()
    const removeItemSpy = vi.spyOn(window.localStorage, 'removeItem')

    const LogoutConsumer = () => {
      const { user, loading, logout } = useAuth()

      if (loading) return <div>loading</div>

      return (
        <div>
          <div data-testid="user-email">{user?.email ?? 'none'}</div>
          <button onClick={() => logout()}>logout</button>
        </div>
      )
    }

    renderWithProvider(<LogoutConsumer />)

    await waitFor(() => expect(screen.getByTestId('user-email')).toHaveTextContent(mockUser.email))

    await userEvent.click(screen.getByText('logout'))

    await waitFor(() => expect(screen.getByTestId('user-email')).toHaveTextContent('none'))
    expect(logoutMutation.mutateAsync).toHaveBeenCalledTimes(1)
    expect(removeItemSpy).not.toHaveBeenCalled()
  })
})

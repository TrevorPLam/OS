import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AuthProvider, useAuth } from '../AuthContext'
import { authApi } from '../../api/auth'

vi.mock('../../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}))

const mockedAuthApi = vi.mocked(authApi)

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
  })

  it('hydrates user from profile endpoint without using localStorage', async () => {
    mockedAuthApi.getProfile.mockResolvedValue(mockUser)
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
    mockedAuthApi.getProfile.mockRejectedValue(new Error('no session'))
    mockedAuthApi.login.mockResolvedValue({ user: mockUser, message: 'Login successful' })
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
    expect(mockedAuthApi.login).toHaveBeenCalledWith({ username: 'demo', password: 'pass' })
    expect(setItemSpy).not.toHaveBeenCalled()
  })

  it('clears user state on logout while relying solely on cookies', async () => {
    mockedAuthApi.getProfile.mockResolvedValue(mockUser)
    mockedAuthApi.logout.mockResolvedValue()
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
    expect(mockedAuthApi.logout).toHaveBeenCalledTimes(1)
    expect(removeItemSpy).not.toHaveBeenCalled()
  })
})

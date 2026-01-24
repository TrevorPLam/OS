import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Login from '../Login'

const loginMutation = {
  mutateAsync: vi.fn(),
  reset: vi.fn(),
  isPending: false,
  error: undefined as unknown,
}
const navigateMock = vi.fn()

vi.mock('../../api/auth', () => ({
  useLogin: () => loginMutation,
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

describe('Login form', () => {
  beforeEach(() => {
    loginMutation.mutateAsync.mockReset()
    loginMutation.reset.mockReset()
    loginMutation.error = undefined
    navigateMock.mockReset()
  })

  it('submits credentials and navigates on success', async () => {
    loginMutation.mutateAsync.mockResolvedValueOnce(undefined)
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Username'), 'jane')
    await user.type(screen.getByLabelText('Password'), 'secret')
    await user.click(screen.getByRole('button', { name: 'Sign In' }))

    expect(loginMutation.mutateAsync).toHaveBeenCalledWith({ username: 'jane', password: 'secret' })
    expect(navigateMock).toHaveBeenCalledWith('/')
  })

  it('shows an error message when login fails', async () => {
    loginMutation.error = { response: { data: { error: 'Invalid credentials' } } }
    loginMutation.mutateAsync.mockRejectedValueOnce(
      loginMutation.error
    )
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Username'), 'jane')
    await user.type(screen.getByLabelText('Password'), 'badpass')
    await user.click(screen.getByRole('button', { name: 'Sign In' }))

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument()
  })
})

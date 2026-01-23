import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Register from '../Register'

const registerMock = vi.fn()
const navigateMock = vi.fn()

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    register: registerMock,
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

describe('Register form', () => {
  beforeEach(() => {
    registerMock.mockReset()
    navigateMock.mockReset()
  })

  it('submits registration data and navigates on success', async () => {
    registerMock.mockResolvedValueOnce(undefined)
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('First Name'), 'Jane')
    await user.type(screen.getByLabelText('Last Name'), 'Doe')
    await user.type(screen.getByLabelText('Username'), 'janedoe')
    await user.type(screen.getByLabelText('Email'), 'jane@example.com')
    await user.type(screen.getByLabelText('Password'), 'secret123')
    await user.type(screen.getByLabelText('Confirm Password'), 'secret123')
    await user.click(screen.getByRole('button', { name: 'Sign Up' }))

    expect(registerMock).toHaveBeenCalledWith({
      username: 'janedoe',
      email: 'jane@example.com',
      first_name: 'Jane',
      last_name: 'Doe',
      password: 'secret123',
      password2: 'secret123',
    })
    expect(navigateMock).toHaveBeenCalledWith('/')
  })

  it('shows field errors when registration fails', async () => {
    registerMock.mockRejectedValueOnce({ response: { data: { email: ['Invalid email'] } } })
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('First Name'), 'Jane')
    await user.type(screen.getByLabelText('Last Name'), 'Doe')
    await user.type(screen.getByLabelText('Username'), 'janedoe')
    await user.type(screen.getByLabelText('Email'), 'jane@example.com')
    await user.type(screen.getByLabelText('Password'), 'secret123')
    await user.type(screen.getByLabelText('Confirm Password'), 'secret123')
    await user.click(screen.getByRole('button', { name: 'Sign Up' }))

    expect(await screen.findByText('Invalid email')).toBeInTheDocument()
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useProfile, useLogin, useLogout, useRegister } from '../auth'
import apiClient from '../client'
import type { ReactNode } from 'react'

vi.mock('../client')

const createQueryWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('Auth API Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useProfile', () => {
    it('fetches user profile successfully', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
        date_joined: '2024-01-01T00:00:00Z',
      }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const { result } = renderHook(() => useProfile(), {
        wrapper: createQueryWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockUser)
      expect(apiClient.get).toHaveBeenCalledWith('/auth/profile/')
    })

    it('handles profile fetch error', async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Unauthorized'))

      const { result } = renderHook(() => useProfile(), {
        wrapper: createQueryWrapper(),
      })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(new Error('Unauthorized'))
    })
  })

  describe('useLogin', () => {
    it('logs in user successfully', async () => {
      const mockResponse = {
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          date_joined: '2024-01-01T00:00:00Z',
        },
        message: 'Login successful',
      }
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const { result } = renderHook(() => useLogin(), {
        wrapper: createQueryWrapper(),
      })

      const credentials = { username: 'testuser', password: 'password123' }
      result.current.mutate(credentials)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockResponse)
      expect(apiClient.post).toHaveBeenCalledWith('/auth/login/', credentials)
    })

    it('handles login error', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Invalid credentials'))

      const { result } = renderHook(() => useLogin(), {
        wrapper: createQueryWrapper(),
      })

      result.current.mutate({ username: 'testuser', password: 'wrong' })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(new Error('Invalid credentials'))
    })
  })

  describe('useLogout', () => {
    it('logs out user successfully', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ data: {} })

      const { result } = renderHook(() => useLogout(), {
        wrapper: createQueryWrapper(),
      })

      result.current.mutate()

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(apiClient.post).toHaveBeenCalledWith('/auth/logout/')
      expect(result.current.data).toBeUndefined() // useLogout returns void
    })

    it('handles logout error', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Logout failed'))

      const { result } = renderHook(() => useLogout(), {
        wrapper: createQueryWrapper(),
      })

      result.current.mutate()

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(new Error('Logout failed'))
    })
  })

  describe('useRegister', () => {
    it('registers user successfully', async () => {
      const mockResponse = {
        user: {
          id: 2,
          username: 'newuser',
          email: 'new@example.com',
          first_name: 'New',
          last_name: 'User',
          date_joined: '2024-01-20T00:00:00Z',
        },
        message: 'Registration successful',
      }
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const { result } = renderHook(() => useRegister(), {
        wrapper: createQueryWrapper(),
      })

      const registrationData = {
        username: 'newuser',
        email: 'new@example.com',
        first_name: 'New',
        last_name: 'User',
        password: 'password123',
        password2: 'password123',
      }
      result.current.mutate(registrationData)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockResponse)
      expect(apiClient.post).toHaveBeenCalledWith('/auth/register/', registrationData)
    })

    it('handles registration error (password mismatch)', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Passwords do not match'))

      const { result } = renderHook(() => useRegister(), {
        wrapper: createQueryWrapper(),
      })

      const registrationData = {
        username: 'newuser',
        email: 'new@example.com',
        first_name: 'New',
        last_name: 'User',
        password: 'password123',
        password2: 'different',
      }
      result.current.mutate(registrationData)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(new Error('Passwords do not match'))
    })
  })
})

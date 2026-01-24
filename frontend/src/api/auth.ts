import { useMutation, useQuery, useQueryClient, UseMutationResult, UseQueryResult } from '@tanstack/react-query'
import apiClient from './client'

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  date_joined: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  first_name: string
  last_name: string
  password: string
  password2: string
}

export interface AuthResponse {
  user: User
  message: string
}

export const useProfile = (): UseQueryResult<User, Error> => {
  return useQuery({
    queryKey: ['auth', 'profile'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/profile/')
      return response.data
    },
    retry: false,
  })
}

export const useLogin = (): UseMutationResult<AuthResponse, Error, LoginRequest> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (credentials) => {
      const response = await apiClient.post('/auth/login/', credentials)
      return response.data
    },
    onSuccess: (response) => {
      queryClient.setQueryData(['auth', 'profile'], response.user)
    },
  })
}

export const useRegister = (): UseMutationResult<AuthResponse, Error, RegisterRequest> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/auth/register/', data)
      return response.data
    },
    onSuccess: (response) => {
      queryClient.setQueryData(['auth', 'profile'], response.user)
    },
  })
}

export const useLogout = (): UseMutationResult<void, Error, void> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      await apiClient.post('/auth/logout/')
    },
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ['auth', 'profile'] })
    },
  })
}

export const useChangePassword = (): UseMutationResult<
  void,
  Error,
  { oldPassword: string; newPassword: string }
> => {
  return useMutation({
    mutationFn: async ({ oldPassword, newPassword }) => {
      await apiClient.put('/auth/change-password/', {
        old_password: oldPassword,
        new_password: newPassword,
      })
    },
  })
}

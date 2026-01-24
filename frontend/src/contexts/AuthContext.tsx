import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { LoginRequest, RegisterRequest, User, useLogin, useLogout, useProfile, useRegister } from '../api/auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const { data: profile, isLoading } = useProfile()
  const loginMutation = useLogin()
  const registerMutation = useRegister()
  const logoutMutation = useLogout()

  useEffect(() => {
    if (profile) {
      setUser(profile)
      return
    }

    if (!isLoading) {
      setUser(null)
    }
  }, [isLoading, profile])

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await loginMutation.mutateAsync(credentials)
      setUser(response.user)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const register = async (data: RegisterRequest) => {
    try {
      const response = await registerMutation.mutateAsync(data)
      setUser(response.user)
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await logoutMutation.mutateAsync()
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      setUser(null)
    }
  }

  const value = {
    user,
    loading: isLoading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useLogin } from '../api/auth'
import './Auth.css'

type LoginErrorResponse = {
  error?: string
}

const getLoginErrorMessage = (error: unknown): string => {
  if (!error) {
    return ''
  }

  if (typeof error === 'object' && error !== null && 'response' in error) {
    const responseData = (error as { response?: { data?: LoginErrorResponse } }).response?.data
    if (responseData?.error) {
      return responseData.error
    }
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return 'Login failed. Please try again.'
}

const Login: React.FC = () => {
  const navigate = useNavigate()
  const loginMutation = useLogin()

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    loginMutation.reset()

    try {
      await loginMutation.mutateAsync(formData)
      navigate('/')
    } catch {
      // Errors are surfaced via the mutation state.
    }
  }

  const errorMessage = getLoginErrorMessage(loginMutation.error)

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>UBOS</h1>
          <p>Sign in to your account</p>
        </div>

        {errorMessage && (
          <div className="error-message">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/register">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login

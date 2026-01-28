import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useRegister } from '../api/auth'
import './Auth.css'

type RegisterErrorResponse = Record<string, string[]>

const getRegisterFieldErrors = (error: unknown): RegisterErrorResponse => {
  if (!error) {
    return {}
  }

  if (typeof error === 'object' && error !== null && 'response' in error) {
    const responseData = (error as { response?: { data?: RegisterErrorResponse } }).response?.data
    if (responseData && typeof responseData === 'object') {
      return responseData
    }
  }

  return {}
}

const Register: React.FC = () => {
  const navigate = useNavigate()
  const registerMutation = useRegister()

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    password2: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    registerMutation.reset()

    try {
      await registerMutation.mutateAsync(formData)
      navigate('/')
    } catch {
      // Errors are surfaced via the mutation state.
    }
  }

  const errors = getRegisterFieldErrors(registerMutation.error)

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>UBOS</h1>
          <p>Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">First Name</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
              />
              {errors.first_name && (
                <span className="field-error">{errors.first_name[0]}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Last Name</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                required
              />
              {errors.last_name && (
                <span className="field-error">{errors.last_name[0]}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
            />
            {errors.username && (
              <span className="field-error">{errors.username[0]}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
            {errors.email && (
              <span className="field-error">{errors.email[0]}</span>
            )}
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
            {errors.password && (
              <span className="field-error">{errors.password[0]}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password2">Confirm Password</label>
            <input
              type="password"
              id="password2"
              name="password2"
              value={formData.password2}
              onChange={handleChange}
              required
            />
            {errors.password2 && (
              <span className="field-error">{errors.password2[0]}</span>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={registerMutation.isPending}
          >
            {registerMutation.isPending ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register

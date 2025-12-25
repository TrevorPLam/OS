import axios from 'axios'

const broadcastImpersonationStatus = (headers: Record<string, any>) => {
  const rawHeader = headers['x-break-glass-impersonation']

  if (rawHeader) {
    try {
      const parsed = typeof rawHeader === 'string' ? JSON.parse(rawHeader) : rawHeader
      window.dispatchEvent(new CustomEvent('impersonation-status', { detail: { active: true, ...parsed } }))
      return
    } catch (error) {
      console.warn('Failed to parse impersonation header', error)
    }
  }

  window.dispatchEvent(new CustomEvent('impersonation-status', { detail: { active: false } }))
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => {
    broadcastImpersonationStatus(response.headers || {})
    return response
  },
  async (error) => {
    const originalRequest = error.config

    if (error.response?.headers) {
      broadcastImpersonationStatus(error.response.headers)
    }

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          })

          const { access } = response.data
          localStorage.setItem('access_token', access)

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient

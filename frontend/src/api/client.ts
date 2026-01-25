import axios, { AxiosError, AxiosHeaderValue, AxiosRequestConfig } from 'axios'

// Narrow header values to known shapes so lint stays strict without blocking axios headers.
type HeaderValue = AxiosHeaderValue | AxiosHeaderValue[] | undefined

const broadcastImpersonationStatus = (headers: Record<string, HeaderValue>) => {
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

type RetriableRequestConfig = AxiosRequestConfig & { _retry?: boolean }

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => {
    broadcastImpersonationStatus(response.headers || {})
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableRequestConfig

    if (error.response?.headers) {
      broadcastImpersonationStatus(error.response.headers)
    }

    const status = error.response?.status
    const requestUrl = originalRequest?.url || ''
    const isAuthRoute = ['/auth/login/', '/auth/register/', '/auth/logout/'].some((path) =>
      requestUrl.includes(path)
    )
    const isRefreshRoute = requestUrl.includes('/auth/token/refresh/')

    if (status === 401 && originalRequest && !originalRequest._retry && !isAuthRoute && !isRefreshRoute) {
      originalRequest._retry = true

      try {
        await apiClient.post('/auth/token/refresh/')
        return apiClient(originalRequest)
      } catch (refreshError) {
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient

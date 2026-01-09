import type { AxiosError } from 'axios'

const createMock = vi.fn()
let responseHandlers: {
  onFulfilled?: (response: { headers?: Record<string, string> }) => unknown
  onRejected?: (error: AxiosError) => Promise<unknown>
}
let mockInstance: ReturnType<typeof vi.fn>
let mockPost: ReturnType<typeof vi.fn>

const buildMockInstance = () => {
  responseHandlers = {}
  mockPost = vi.fn()
  mockInstance = vi.fn()
  mockInstance.post = mockPost
  mockInstance.interceptors = {
    response: {
      use: vi.fn((onFulfilled, onRejected) => {
        responseHandlers.onFulfilled = onFulfilled
        responseHandlers.onRejected = onRejected
      }),
    },
  }
  return mockInstance
}

vi.mock('axios', () => ({
  default: {
    create: (...args: unknown[]) => createMock(...args),
  },
  create: (...args: unknown[]) => createMock(...args),
}))

describe('api client', () => {
  beforeEach(() => {
    vi.resetModules()
    createMock.mockReset()
    buildMockInstance()
    createMock.mockImplementation(() => mockInstance)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('creates axios client with expected defaults', async () => {
    await import('../client')

    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: expect.any(String),
        headers: { 'Content-Type': 'application/json' },
        withCredentials: true,
      })
    )
  })

  it('broadcasts impersonation status when header is present', async () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    await import('../client')

    expect(responseHandlers.onFulfilled).toBeDefined()

    const response = {
      headers: {
        'x-break-glass-impersonation': JSON.stringify({ active: true, user_id: 42 }),
      },
    }

    responseHandlers.onFulfilled!(response)

    expect(dispatchSpy).toHaveBeenCalledTimes(1)
    const event = dispatchSpy.mock.calls[0][0] as CustomEvent
    expect(event.type).toBe('impersonation-status')
    expect(event.detail).toMatchObject({ active: true, user_id: 42 })
  })

  it('refreshes token and retries request on 401 responses', async () => {
    await import('../client')

    const retriedResponse = { data: 'ok' }
    mockPost.mockResolvedValue({})
    mockInstance.mockResolvedValue(retriedResponse)

    const error = {
      response: { status: 401, headers: {} },
      config: { url: '/api/v1/clients/', headers: {} },
    } as AxiosError

    expect(responseHandlers.onRejected).toBeDefined()
    const result = await responseHandlers.onRejected!(error)

    expect(mockPost).toHaveBeenCalledWith('/auth/token/refresh/')
    expect(mockInstance).toHaveBeenCalledWith(expect.objectContaining({ url: '/api/v1/clients/', _retry: true }))
    expect(result).toBe(retriedResponse)
  })

  it('does not attempt refresh for auth routes', async () => {
    await import('../client')

    const error = {
      response: { status: 401, headers: {} },
      config: { url: '/auth/login/', headers: {} },
    } as AxiosError

    expect(responseHandlers.onRejected).toBeDefined()
    await expect(responseHandlers.onRejected!(error)).rejects.toBe(error)
    expect(mockPost).not.toHaveBeenCalled()
  })
})

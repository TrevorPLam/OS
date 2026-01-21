import { beforeEach, describe, expect, it, vi } from 'vitest'

import apiClient from '../client'
import { clientPortalApi } from '../clientPortal'
import { portalDocumentsApi } from '../documents'

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

type MockedApiClient = {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const mockedClient = apiClient as MockedApiClient

describe('clientPortalApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('test_listProjects_uses_portal_endpoint', async () => {
    // Happy path: ensure portal projects stay on the portal allowlist namespace.
    mockedClient.get.mockResolvedValueOnce({ data: { results: [{ id: 1 }] } })

    const response = await clientPortalApi.listProjects()

    expect(mockedClient.get).toHaveBeenCalledWith('/portal/projects/', { params: undefined })
    expect(response.data.results).toHaveLength(1)
  })

  it('test_listInvoices_allows_empty_results', async () => {
    // Empty state: portal invoices can legitimately return zero results.
    mockedClient.get.mockResolvedValueOnce({ data: { results: [] } })

    const response = await clientPortalApi.listInvoices()

    expect(mockedClient.get).toHaveBeenCalledWith('/portal/invoices/', { params: undefined })
    expect(response.data.results).toEqual([])
  })

  it('test_getInvoiceSummary_propagates_errors', async () => {
    // Error handling: bubble up network failures to the caller.
    mockedClient.get.mockRejectedValueOnce(new Error('network down'))

    await expect(clientPortalApi.getInvoiceSummary()).rejects.toThrow('network down')
  })
})

describe('portalDocumentsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('test_getDocuments_returns_portal_results', async () => {
    // Happy path: portal document listing stays within the portal namespace.
    mockedClient.get.mockResolvedValueOnce({ data: { results: [{ id: 42 }] } })

    const documents = await portalDocumentsApi.getDocuments()

    expect(mockedClient.get).toHaveBeenCalledWith('/portal/documents/', { params: undefined })
    expect(documents).toHaveLength(1)
  })

  it('test_getFolders_handles_empty_results', async () => {
    // Empty state: no folders should return an empty list without error.
    mockedClient.get.mockResolvedValueOnce({ data: { results: [] } })

    const folders = await portalDocumentsApi.getFolders()

    expect(mockedClient.get).toHaveBeenCalledWith('/portal/folders/', { params: undefined })
    expect(folders).toEqual([])
  })

  it('test_downloadDocument_propagates_errors', async () => {
    // Error handling: download failures should propagate to the caller.
    mockedClient.get.mockRejectedValueOnce(new Error('download failed'))

    await expect(portalDocumentsApi.downloadDocument(12)).rejects.toThrow('download failed')
    expect(mockedClient.get).toHaveBeenCalledWith('/portal/documents/12/download/')
  })
})

import { beforeEach, describe, expect, it, vi } from 'vitest'

import apiClient from '../client'
import { clientPortalApi } from '../clientPortal'
import { portalDocumentsApi } from '../documents'

vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

type MockedApiClient = {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
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

  it('test_listAppointmentTypes_returns_available_types', async () => {
    // Happy path: appointment types should be returned as a list for portal booking.
    mockedClient.get.mockResolvedValueOnce({ data: [{ id: 7, name: 'Kickoff' }] })

    const response = await clientPortalApi.listAppointmentTypes()

    expect(mockedClient.get).toHaveBeenCalledWith('/portal/appointments/available-types/')
    expect(response.data).toHaveLength(1)
  })

  it('test_listAvailableAppointmentSlots_allows_empty_slots', async () => {
    // Empty state: no slots should still return a valid response.
    mockedClient.post.mockResolvedValueOnce({ data: { slots: [] } })

    const response = await clientPortalApi.listAvailableAppointmentSlots({
      appointment_type_id: 3,
      start_date: '2026-01-01',
      end_date: '2026-01-14',
    })

    expect(mockedClient.post).toHaveBeenCalledWith('/portal/appointments/available-slots/', {
      appointment_type_id: 3,
      start_date: '2026-01-01',
      end_date: '2026-01-14',
    })
    expect(response.data.slots).toEqual([])
  })

  it('test_bookAppointment_propagates_errors', async () => {
    // Error handling: booking failures should be reported to callers.
    mockedClient.post.mockRejectedValueOnce(new Error('booking failed'))

    await expect(clientPortalApi.bookAppointment({
      appointment_type_id: 9,
      start_time: '2026-01-05T10:00:00Z',
    })).rejects.toThrow('booking failed')
  })

  it('test_getProfile_returns_portal_profile', async () => {
    // Happy path: portal profile uses the allowlisted portal endpoint.
    mockedClient.get.mockResolvedValueOnce({ data: { id: 1, email: 'client@example.com' } })

    const response = await clientPortalApi.getProfile()

    expect(mockedClient.get).toHaveBeenCalledWith('/portal/profile/me/')
    expect(response.data.email).toBe('client@example.com')
  })

  it('test_listAccounts_handles_empty_accounts', async () => {
    // Empty state: account switcher should handle an empty account list gracefully.
    mockedClient.get.mockResolvedValueOnce({
      data: { accounts: [], current_account_id: 1, has_multiple_accounts: false },
    })

    const response = await clientPortalApi.listAccounts()

    expect(mockedClient.get).toHaveBeenCalledWith('/portal/accounts/accounts/')
    expect(response.data.accounts).toEqual([])
  })

  it('test_updateProfile_propagates_errors', async () => {
    // Error handling: profile update failures should bubble to the caller.
    mockedClient.patch.mockRejectedValueOnce(new Error('update failed'))

    await expect(clientPortalApi.updateProfile({ notification_preferences: {} })).rejects.toThrow('update failed')
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

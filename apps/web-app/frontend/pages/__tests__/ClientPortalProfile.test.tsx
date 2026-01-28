import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ClientPortal } from '../ClientPortal'

const portalDocumentsApiMock = vi.hoisted(() => ({
  getDocuments: vi.fn(),
}))

const clientPortalApiMock = vi.hoisted(() => ({
  listProjects: vi.fn(),
  listInvoices: vi.fn(),
  getInvoiceSummary: vi.fn(),
  listProposals: vi.fn(),
  listContracts: vi.fn(),
  listEngagementHistory: vi.fn(),
  getActiveThread: vi.fn(),
  listAppointments: vi.fn(),
  listAppointmentTypes: vi.fn(),
  listAvailableAppointmentSlots: vi.fn(),
  bookAppointment: vi.fn(),
  cancelAppointment: vi.fn(),
  getProfile: vi.fn(),
  updateProfile: vi.fn(),
  listAccounts: vi.fn(),
  switchAccount: vi.fn(),
}))

vi.mock('../../api/documents', () => ({
  portalDocumentsApi: portalDocumentsApiMock,
}))

vi.mock('../../api/clientPortal', () => ({
  clientPortalApi: clientPortalApiMock,
}))

const baseInvoiceSummary = {
  total_invoices: 0,
  total_billed: 0,
  total_paid: 0,
  total_outstanding: 0,
  overdue_count: 0,
  by_status: {},
}

const baseThreadResponse = {
  id: 1,
  client: 1,
  client_name: 'Acme Co',
  date: '2026-01-10',
  is_active: true,
  archived_at: null,
  message_count: 0,
  last_message_at: null,
  last_message_by: null,
  last_message_by_name: null,
  created_at: '2026-01-10T09:00:00Z',
  updated_at: '2026-01-10T09:00:00Z',
  messages: [],
  recent_messages: [],
}

const setupBaseMocks = () => {
  clientPortalApiMock.listProjects.mockResolvedValue({ data: { results: [] } })
  portalDocumentsApiMock.getDocuments.mockResolvedValue([])
  clientPortalApiMock.listInvoices.mockResolvedValue({ data: { results: [] } })
  clientPortalApiMock.getInvoiceSummary.mockResolvedValue({ data: baseInvoiceSummary })
  clientPortalApiMock.listProposals.mockResolvedValue({ data: { results: [] } })
  clientPortalApiMock.listContracts.mockResolvedValue({ data: { results: [] } })
  clientPortalApiMock.listEngagementHistory.mockResolvedValue({ data: { results: [] } })
  clientPortalApiMock.getActiveThread.mockResolvedValue({ data: baseThreadResponse })
  clientPortalApiMock.listAppointments.mockResolvedValue({ data: { results: [] } })
  clientPortalApiMock.listAppointmentTypes.mockResolvedValue({ data: [] })
  clientPortalApiMock.listAvailableAppointmentSlots.mockResolvedValue({ data: { slots: [] } })
  clientPortalApiMock.bookAppointment.mockResolvedValue({ data: {} })
  clientPortalApiMock.cancelAppointment.mockResolvedValue({ data: {} })
}

const baseProfile = {
  id: 1,
  email: 'client@example.com',
  full_name: 'Portal User',
  client_name: 'Acme Co',
  can_view_projects: true,
  can_view_invoices: true,
  can_view_documents: true,
  can_upload_documents: false,
  can_message_staff: true,
  can_book_appointments: true,
  notification_preferences: { email: true },
}

describe('ClientPortal profile and accounts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupBaseMocks()
  })

  it('test_profile_happy_path_updates_preferences', async () => {
    // Happy path: portal users can view and update their notification preferences.
    clientPortalApiMock.getProfile.mockResolvedValue({ data: baseProfile })
    clientPortalApiMock.updateProfile.mockResolvedValue({
      data: {
        ...baseProfile,
        notification_preferences: { email: false },
      },
    })
    clientPortalApiMock.listAccounts.mockResolvedValue({
      data: {
        accounts: [{ id: 10, name: 'Acme Co', account_number: 'AC-10' }],
        current_account_id: 10,
        has_multiple_accounts: false,
      },
    })

    const user = userEvent.setup()

    render(<ClientPortal />)

    await screen.findByText('Client Portal')
    await user.click(screen.getByRole('button', { name: '👤 Profile' }))

    expect(await screen.findByText('client@example.com')).toBeInTheDocument()

    const preferencesInput = screen.getByLabelText('Notification preferences')
    await user.clear(preferencesInput)
    // Use paste instead of type to avoid user-event interpreting curly braces as keyboard commands
    await user.click(preferencesInput)
    await user.paste('{"email": false}')
    await user.click(screen.getByRole('button', { name: 'Save preferences' }))

    expect(clientPortalApiMock.updateProfile).toHaveBeenCalledWith({
      notification_preferences: { email: false },
    })
  })

  it('test_profile_empty_accounts_state', async () => {
    // Empty state: show guidance when there are no accounts to switch to.
    clientPortalApiMock.getProfile.mockResolvedValue({ data: baseProfile })
    clientPortalApiMock.listAccounts.mockResolvedValue({
      data: {
        accounts: [],
        current_account_id: 1,
        has_multiple_accounts: false,
      },
    })

    const user = userEvent.setup()

    render(<ClientPortal />)

    await screen.findByText('Client Portal')
    await user.click(screen.getByRole('button', { name: '👤 Profile' }))

    expect(await screen.findByText('No accounts available for switching.')).toBeInTheDocument()
  })

  it('test_profile_error_state', async () => {
    // Error handling: surface failures when profile data cannot load.
    clientPortalApiMock.getProfile.mockRejectedValue(new Error('Network error'))
    clientPortalApiMock.listAccounts.mockResolvedValue({
      data: {
        accounts: [{ id: 10, name: 'Acme Co', account_number: 'AC-10' }],
        current_account_id: 10,
        has_multiple_accounts: false,
      },
    })

    const user = userEvent.setup()

    render(<ClientPortal />)

    await screen.findByText('Client Portal')
    await user.click(screen.getByRole('button', { name: '👤 Profile' }))

    // Check for error display (the component shows the error message in an ErrorDisplay component)
    expect(await screen.findByText('Network error')).toBeInTheDocument()
    expect(screen.getByText('Profile details are unavailable.')).toBeInTheDocument()
  })
})

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

describe('ClientPortal appointments', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupBaseMocks()
  })

  it('test_appointments_happy_path_booking', async () => {
    // Happy path: portal users can fetch slots and book an appointment.
    clientPortalApiMock.listAppointmentTypes.mockResolvedValue({
      data: [
        {
          id: 1,
          name: 'Consultation',
          description: 'Initial discovery call',
          duration_minutes: 30,
          location_mode: 'video',
        },
      ],
    })
    clientPortalApiMock.listAvailableAppointmentSlots.mockResolvedValue({
      data: {
        slots: [
          {
            start_time: '2026-01-10T10:00:00Z',
            end_time: '2026-01-10T10:30:00Z',
          },
        ],
      },
    })

    const user = userEvent.setup()

    render(<ClientPortal />)

    await screen.findByText('Client Portal')
    await user.click(screen.getByRole('button', { name: '🗓️ Appointments' }))

    await user.click(screen.getByRole('button', { name: 'Consultation' }))
    await user.click(screen.getByRole('button', { name: 'Check availability' }))

    const slotButtons = await screen.findAllByRole('button', { name: /→/ })
    await user.click(slotButtons[0])

    await user.type(screen.getByLabelText('Notes (optional)'), 'Please include prep materials.')
    await user.click(screen.getByRole('button', { name: 'Book appointment' }))

    expect(clientPortalApiMock.bookAppointment).toHaveBeenCalledWith({
      appointment_type_id: 1,
      start_time: '2026-01-10T10:00:00Z',
      notes: 'Please include prep materials.',
    })
  })

  it('test_appointments_empty_state', async () => {
    // Empty state: show prompts when there are no appointments or types.
    const user = userEvent.setup()

    render(<ClientPortal />)

    await screen.findByText('Client Portal')
    await user.click(screen.getByRole('button', { name: '🗓️ Appointments' }))

    expect(await screen.findByText('No upcoming appointments yet.')).toBeInTheDocument()
    expect(screen.getByText('No appointment types available.')).toBeInTheDocument()
  })

  it('test_appointments_error_state', async () => {
    // Error handling: surface failures to load appointment data.
    clientPortalApiMock.listAppointmentTypes.mockRejectedValue(new Error('Network failure'))

    const user = userEvent.setup()

    render(<ClientPortal />)

    await screen.findByText('Client Portal')
    await user.click(screen.getByRole('button', { name: '🗓️ Appointments' }))

    expect(await screen.findByText('Unable to load appointment options right now.')).toBeInTheDocument()
  })
})

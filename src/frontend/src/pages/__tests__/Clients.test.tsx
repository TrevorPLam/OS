import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Clients from '../Clients'

const clientsApiMock = vi.hoisted(() => ({
  getClients: vi.fn(),
  createClient: vi.fn(),
  updateClient: vi.fn(),
  deleteClient: vi.fn(),
}))

vi.mock('../../api/clients', () => ({
  clientsApi: clientsApiMock,
}))

describe('Clients form', () => {
  beforeEach(() => {
    clientsApiMock.getClients.mockResolvedValue([])
    clientsApiMock.createClient.mockResolvedValue({})
    clientsApiMock.updateClient.mockResolvedValue({})
    clientsApiMock.deleteClient.mockResolvedValue({})
  })

  it('shows the empty state when no clients exist', async () => {
    render(<Clients />)

    expect(await screen.findByText('No clients yet. Add your first client to get started!')).toBeInTheDocument()
  })

  it('creates a new client from the form', async () => {
    const user = userEvent.setup()

    render(<Clients />)

    await screen.findByText('Clients')
    await user.click(screen.getByRole('button', { name: '+ Add Client' }))

    await user.type(screen.getByLabelText('Company Name *'), 'Acme Co')
    await user.type(screen.getByLabelText('Industry'), 'Manufacturing')
    await user.type(screen.getByLabelText('Primary Contact Name *'), 'Alex Smith')
    await user.type(screen.getByLabelText('Email *'), 'alex@example.com')
    await user.type(screen.getByLabelText('Phone'), '555-0100')

    await user.click(screen.getByRole('button', { name: 'Create Client' }))

    expect(clientsApiMock.createClient).toHaveBeenCalledWith(
      expect.objectContaining({
        company_name: 'Acme Co',
        industry: 'Manufacturing',
        primary_contact_name: 'Alex Smith',
        primary_contact_email: 'alex@example.com',
        primary_contact_phone: '555-0100',
      }),
    )
  })
})

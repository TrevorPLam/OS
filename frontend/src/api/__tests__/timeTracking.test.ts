import { describe, it, expect, vi, beforeEach } from 'vitest'
import { timeTrackingApi } from '../timeTracking'
import apiClient from '../client'

vi.mock('../client')

describe('Time Tracking API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getTimeEntries fetches all time entries', async () => {
    const mockTimeEntries = [
      {
        id: 1,
        project: 1,
        project_name: 'Website Redesign',
        task: 5,
        task_title: 'Design homepage',
        user: 10,
        user_name: 'John Doe',
        date: '2024-01-15',
        hours: '4.5',
        description: 'Worked on homepage design',
        is_billable: true,
        hourly_rate: '150',
        billed_amount: '675',
        invoiced: false,
        created_at: '2024-01-15T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockTimeEntries })

    const result = await timeTrackingApi.getTimeEntries()

    expect(result).toEqual(mockTimeEntries)
    expect(apiClient.get).toHaveBeenCalledWith('/projects/time-entries/')
  })

  it('getTimeEntries handles paginated results', async () => {
    const mockTimeEntries = [
      {
        id: 2,
        project: 2,
        user: 11,
        date: '2024-01-16',
        hours: '2.0',
        description: 'Code review',
        is_billable: true,
        hourly_rate: '150',
        billed_amount: '300',
        invoiced: false,
        created_at: '2024-01-16T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: { results: mockTimeEntries } })

    const result = await timeTrackingApi.getTimeEntries()

    expect(result).toEqual(mockTimeEntries)
  })

  it('createTimeEntry creates a new time entry', async () => {
    const newTimeEntry = {
      project: 1,
      task: 5,
      user: 10,
      date: '2024-01-20',
      hours: '3.0',
      description: 'Implemented feature',
      is_billable: true,
      hourly_rate: '150',
      billed_amount: '450',
      invoiced: false,
    }
    const createdTimeEntry = {
      ...newTimeEntry,
      id: 3,
      created_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdTimeEntry })

    const result = await timeTrackingApi.createTimeEntry(newTimeEntry)

    expect(result).toEqual(createdTimeEntry)
    expect(apiClient.post).toHaveBeenCalledWith('/projects/time-entries/', newTimeEntry)
  })

  it('updateTimeEntry updates a time entry', async () => {
    const updatedTimeEntry = {
      id: 1,
      project: 1,
      task: 5,
      user: 10,
      date: '2024-01-15',
      hours: '5.0',
      description: 'Worked on homepage design - extended',
      is_billable: true,
      hourly_rate: '150',
      billed_amount: '750',
      invoiced: false,
      created_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedTimeEntry })

    const result = await timeTrackingApi.updateTimeEntry(1, { hours: '5.0', billed_amount: '750' })

    expect(result).toEqual(updatedTimeEntry)
    expect(apiClient.put).toHaveBeenCalledWith('/projects/time-entries/1/', { hours: '5.0', billed_amount: '750' })
  })

  it('deleteTimeEntry deletes a time entry', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    await timeTrackingApi.deleteTimeEntry(1)

    expect(apiClient.delete).toHaveBeenCalledWith('/projects/time-entries/1/')
  })

  it('getProjects fetches all projects', async () => {
    const mockProjects = [
      {
        id: 1,
        client: 10,
        client_name: 'Acme Corp',
        project_code: 'PROJ-001',
        name: 'Website Redesign',
        status: 'in_progress',
        billing_type: 'time_and_materials',
        hourly_rate: '150',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockProjects })

    const result = await timeTrackingApi.getProjects()

    expect(result).toEqual(mockProjects)
    expect(apiClient.get).toHaveBeenCalledWith('/projects/projects/')
  })

  it('getProjects handles paginated results', async () => {
    const mockProjects = [
      {
        id: 2,
        client: 11,
        project_code: 'PROJ-002',
        name: 'Mobile App',
        status: 'planning',
        billing_type: 'fixed_price',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: { results: mockProjects } })

    const result = await timeTrackingApi.getProjects()

    expect(result).toEqual(mockProjects)
  })
})

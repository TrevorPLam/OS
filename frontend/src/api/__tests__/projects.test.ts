import { describe, it, expect, vi, beforeEach } from 'vitest'
import { projectsApi } from '../projects'
import apiClient from '../client'

vi.mock('../client')

describe('Projects API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getProjects fetches projects list', async () => {
    const mockProjects = [
      { id: 1, name: 'Website Redesign', client: 1, contract: 100, project_manager: 10, project_code: 'PROJ-001', description: 'Redesign company website', status: 'in_progress', billing_type: 'fixed_price', budget: '50000', hourly_rate: null, start_date: '2024-01-01', end_date: '2024-06-30', actual_completion_date: null, created_at: '2024-01-01', updated_at: '2024-01-15', notes: 'On track' },
      { id: 2, name: 'Mobile App', client: 2, contract: 101, project_manager: 11, project_code: 'PROJ-002', description: 'Build mobile app', status: 'planning', billing_type: 'time_and_materials', budget: null, hourly_rate: '150', start_date: '2024-02-01', end_date: '2024-08-31', actual_completion_date: null, created_at: '2024-02-01', updated_at: '2024-02-10', notes: '' },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockProjects })

    const result = await projectsApi.getProjects()

    expect(result).toEqual(mockProjects)
    expect(apiClient.get).toHaveBeenCalledWith('/projects/projects/')
  })

  it('getProjects handles paginated results', async () => {
    const mockProjects = [
      { id: 1, name: 'Website Redesign', client: 1, contract: 100, project_manager: 10, project_code: 'PROJ-001', description: 'Redesign company website', status: 'in_progress', billing_type: 'fixed_price', budget: '50000', hourly_rate: null, start_date: '2024-01-01', end_date: '2024-06-30', actual_completion_date: null, created_at: '2024-01-01', updated_at: '2024-01-15', notes: 'On track' },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: { results: mockProjects } })

    const result = await projectsApi.getProjects()

    expect(result).toEqual(mockProjects)
  })

  it('getProject fetches single project', async () => {
    const mockProject = { id: 1, name: 'Website Redesign', client: 1, contract: 100, project_manager: 10, project_code: 'PROJ-001', description: 'Redesign company website', status: 'in_progress', billing_type: 'fixed_price', budget: '50000', hourly_rate: null, start_date: '2024-01-01', end_date: '2024-06-30', actual_completion_date: null, created_at: '2024-01-01', updated_at: '2024-01-15', notes: 'On track' }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockProject })

    const result = await projectsApi.getProject(1)

    expect(result).toEqual(mockProject)
    expect(apiClient.get).toHaveBeenCalledWith('/projects/projects/1/')
  })

  it('createProject creates a new project', async () => {
    const newProject = { client: 1, project_code: 'PROJ-003', name: 'New Project', status: 'planning' as const, billing_type: 'fixed_price' as const, start_date: '2024-03-01', end_date: '2024-09-30' }
    const createdProject = { ...newProject, id: 3, contract: null, project_manager: null, description: '', budget: null, hourly_rate: null, actual_completion_date: null, notes: '', created_at: '2024-01-20', updated_at: '2024-01-20' }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdProject })

    const result = await projectsApi.createProject(newProject)

    expect(result).toEqual(createdProject)
    expect(apiClient.post).toHaveBeenCalledWith('/projects/projects/', newProject)
  })

  it('updateProject updates a project', async () => {
    const updatedProject = { id: 1, name: 'Website Redesign - Updated', client: 1, contract: 100, project_manager: 10, project_code: 'PROJ-001', description: 'Redesign company website', status: 'in_progress', billing_type: 'fixed_price', budget: '55000', hourly_rate: null, start_date: '2024-01-01', end_date: '2024-06-30', actual_completion_date: null, created_at: '2024-01-01', updated_at: '2024-01-21', notes: 'On track' }
    vi.mocked(apiClient.patch).mockResolvedValue({ data: updatedProject })

    const result = await projectsApi.updateProject(1, { name: 'Website Redesign - Updated', budget: '55000' })

    expect(result).toEqual(updatedProject)
    expect(apiClient.patch).toHaveBeenCalledWith('/projects/projects/1/', { name: 'Website Redesign - Updated', budget: '55000' })
  })

  it('deleteProject deletes a project', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    await projectsApi.deleteProject(1)

    expect(apiClient.delete).toHaveBeenCalledWith('/projects/projects/1/')
  })
})

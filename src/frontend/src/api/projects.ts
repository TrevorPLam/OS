import apiClient from './client'

export interface Project {
  id: number
  client: number
  contract: number | null
  project_manager: number | null
  project_code: string
  name: string
  description: string
  status: 'planning' | 'in_progress' | 'on_hold' | 'completed' | 'cancelled'
  billing_type: 'fixed_price' | 'time_and_materials' | 'retainer' | 'non_billable'
  budget: string | null
  hourly_rate: string | null
  start_date: string
  end_date: string
  actual_completion_date: string | null
  created_at: string
  updated_at: string
  notes: string
}

export interface ProjectCreate {
  client: number
  contract?: number | null
  project_manager?: number | null
  project_code: string
  name: string
  description?: string
  status?: 'planning' | 'in_progress' | 'on_hold' | 'completed' | 'cancelled'
  billing_type?: 'fixed_price' | 'time_and_materials' | 'retainer' | 'non_billable'
  budget?: string | null
  hourly_rate?: string | null
  start_date: string
  end_date: string
  actual_completion_date?: string | null
  notes?: string
}

export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get('/projects/projects/')
    return response.data.results || response.data
  },

  getProject: async (id: number): Promise<Project> => {
    const response = await apiClient.get(`/projects/projects/${id}/`)
    return response.data
  },

  createProject: async (project: ProjectCreate): Promise<Project> => {
    const response = await apiClient.post('/projects/projects/', project)
    return response.data
  },

  updateProject: async (id: number, project: Partial<Project>): Promise<Project> => {
    const response = await apiClient.patch(`/projects/projects/${id}/`, project)
    return response.data
  },

  deleteProject: async (id: number): Promise<void> => {
    await apiClient.delete(`/projects/projects/${id}/`)
  },
}

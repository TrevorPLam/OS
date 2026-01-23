import apiClient from './client'

export interface TimeEntry {
  id: number
  project: number
  project_name?: string
  task?: number
  task_title?: string
  user: number
  user_name?: string
  date: string
  hours: string
  description: string
  is_billable: boolean
  hourly_rate: string
  billed_amount: string
  invoiced: boolean
  created_at: string
}

export interface Project {
  id: number
  client: number
  client_name?: string
  project_code: string
  name: string
  status: string
  billing_type: string
  hourly_rate?: string
}

export const timeTrackingApi = {
  getTimeEntries: async (): Promise<TimeEntry[]> => {
    const response = await apiClient.get('/projects/time-entries/')
    return response.data.results || response.data
  },

  createTimeEntry: async (data: Partial<TimeEntry>): Promise<TimeEntry> => {
    const response = await apiClient.post('/projects/time-entries/', data)
    return response.data
  },

  updateTimeEntry: async (id: number, data: Partial<TimeEntry>): Promise<TimeEntry> => {
    const response = await apiClient.put(`/projects/time-entries/${id}/`, data)
    return response.data
  },

  deleteTimeEntry: async (id: number): Promise<void> => {
    await apiClient.delete(`/projects/time-entries/${id}/`)
  },

  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get('/projects/projects/')
    return response.data.results || response.data
  },
}

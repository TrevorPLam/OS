import apiClient from './client'

export interface Task {
  id: number
  project: number
  assigned_to: number | null
  title: string
  description: string
  status: 'todo' | 'in_progress' | 'blocked' | 'review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  position: number
  estimated_hours: string | null
  due_date: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  project: number
  assigned_to?: number | null
  title: string
  description?: string
  status?: 'todo' | 'in_progress' | 'blocked' | 'review' | 'done'
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  position?: number
  estimated_hours?: string | null
  due_date?: string | null
}

export const tasksApi = {
  getTasks: async (projectId?: number): Promise<Task[]> => {
    const params = projectId ? { project: projectId } : {}
    const response = await apiClient.get('/projects/tasks/', { params })
    return response.data.results || response.data
  },

  getTask: async (id: number): Promise<Task> => {
    const response = await apiClient.get(`/projects/tasks/${id}/`)
    return response.data
  },

  createTask: async (task: TaskCreate): Promise<Task> => {
    const response = await apiClient.post('/projects/tasks/', task)
    return response.data
  },

  updateTask: async (id: number, task: Partial<Task>): Promise<Task> => {
    const response = await apiClient.patch(`/projects/tasks/${id}/`, task)
    return response.data
  },

  deleteTask: async (id: number): Promise<void> => {
    await apiClient.delete(`/projects/tasks/${id}/`)
  },

  updateTaskStatus: async (id: number, status: Task['status'], position: number): Promise<Task> => {
    const response = await apiClient.patch(`/projects/tasks/${id}/`, { status, position })
    return response.data
  },
}

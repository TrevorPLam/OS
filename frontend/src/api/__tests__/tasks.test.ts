import { describe, it, expect, vi, beforeEach } from 'vitest'
import { tasksApi } from '../tasks'
import apiClient from '../client'

vi.mock('../client')

describe('Tasks API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getTasks fetches all tasks', async () => {
    const mockTasks = [
      {
        id: 1,
        project: 1,
        assigned_to: 5,
        title: 'Implement feature',
        description: 'Build the new feature',
        status: 'in_progress' as const,
        priority: 'high' as const,
        position: 1,
        estimated_hours: '8',
        due_date: '2024-02-01',
        completed_at: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockTasks })

    const result = await tasksApi.getTasks()

    expect(result).toEqual(mockTasks)
    expect(apiClient.get).toHaveBeenCalledWith('/projects/tasks/', { params: {} })
  })

  it('getTasks fetches tasks for a specific project', async () => {
    const mockTasks = [
      {
        id: 2,
        project: 2,
        assigned_to: 5,
        title: 'Write tests',
        description: 'Add unit tests',
        status: 'todo' as const,
        priority: 'medium' as const,
        position: 2,
        estimated_hours: '4',
        due_date: '2024-02-05',
        completed_at: null,
        created_at: '2024-01-10T00:00:00Z',
        updated_at: '2024-01-10T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: { results: mockTasks } })

    const result = await tasksApi.getTasks(2)

    expect(result).toEqual(mockTasks)
    expect(apiClient.get).toHaveBeenCalledWith('/projects/tasks/', { params: { project: 2 } })
  })

  it('getTask fetches a single task', async () => {
    const mockTask = {
      id: 1,
      project: 1,
      assigned_to: 5,
      title: 'Implement feature',
      description: 'Build the new feature',
      status: 'in_progress' as const,
      priority: 'high' as const,
      position: 1,
      estimated_hours: '8',
      due_date: '2024-02-01',
      completed_at: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockTask })

    const result = await tasksApi.getTask(1)

    expect(result).toEqual(mockTask)
    expect(apiClient.get).toHaveBeenCalledWith('/projects/tasks/1/')
  })

  it('createTask creates a new task', async () => {
    const newTask = {
      project: 1,
      assigned_to: 5,
      title: 'New task',
      description: 'Task description',
      status: 'todo' as const,
      priority: 'low' as const,
    }
    const createdTask = {
      ...newTask,
      id: 3,
      position: 3,
      estimated_hours: null,
      due_date: null,
      completed_at: null,
      created_at: '2024-01-20T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdTask })

    const result = await tasksApi.createTask(newTask)

    expect(result).toEqual(createdTask)
    expect(apiClient.post).toHaveBeenCalledWith('/projects/tasks/', newTask)
  })

  it('updateTask updates a task', async () => {
    const updatedTask = {
      id: 1,
      project: 1,
      assigned_to: 5,
      title: 'Implement feature - Updated',
      description: 'Build the new feature',
      status: 'review' as const,
      priority: 'high' as const,
      position: 1,
      estimated_hours: '8',
      due_date: '2024-02-01',
      completed_at: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.patch).mockResolvedValue({ data: updatedTask })

    const result = await tasksApi.updateTask(1, { title: 'Implement feature - Updated', status: 'review' })

    expect(result).toEqual(updatedTask)
    expect(apiClient.patch).toHaveBeenCalledWith('/projects/tasks/1/', { title: 'Implement feature - Updated', status: 'review' })
  })

  it('deleteTask deletes a task', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    await tasksApi.deleteTask(1)

    expect(apiClient.delete).toHaveBeenCalledWith('/projects/tasks/1/')
  })

  it('updateTaskStatus updates task status and position', async () => {
    const updatedTask = {
      id: 1,
      project: 1,
      assigned_to: 5,
      title: 'Implement feature',
      description: 'Build the new feature',
      status: 'done' as const,
      priority: 'high' as const,
      position: 5,
      estimated_hours: '8',
      due_date: '2024-02-01',
      completed_at: '2024-01-20T00:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.patch).mockResolvedValue({ data: updatedTask })

    const result = await tasksApi.updateTaskStatus(1, 'done', 5)

    expect(result).toEqual(updatedTask)
    expect(apiClient.patch).toHaveBeenCalledWith('/projects/tasks/1/', { status: 'done', position: 5 })
  })
})

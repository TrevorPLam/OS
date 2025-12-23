/**
 * API client for Client Portal endpoints
 *
 * Provides client-facing APIs for projects, tasks, and comments
 */
import apiClient from './client';

export interface ClientProject {
  id: number;
  project_code: string;
  name: string;
  description: string;
  status: 'planning' | 'in_progress' | 'completed' | 'on_hold' | 'cancelled';
  budget: string;
  start_date: string;
  end_date: string;
  actual_completion_date: string | null;
  created_at: string;
  updated_at: string;
  project_manager_name: string;
  tasks: ClientTask[];
  total_hours_logged: number;
  progress_percentage: number;
  tasks_summary: {
    todo: number;
    in_progress: number;
    review: number;
    done: number;
    total: number;
  };
}

export interface ClientTask {
  id: number;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'review' | 'done';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  position: number;
  estimated_hours: number | null;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  assigned_to_name: string | null;
  hours_logged: number;
  comments: ClientCommentPreview[];
  progress_percentage: number;
}

export interface ClientCommentPreview {
  id: number;
  author_name: string;
  comment: string;
  created_at: string;
}

export interface ClientComment {
  id: number;
  client: number;
  client_name: string;
  task: number;
  task_title: string;
  task_project: {
    id: number;
    name: string;
    project_code: string | null;
  } | null;
  author: number;
  author_name: string;
  author_email: string;
  comment: string;
  has_attachment: boolean;
  is_read_by_firm: boolean;
  read_by: number | null;
  read_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateCommentData {
  task: number;
  comment: string;
  has_attachment?: boolean;
}

/**
 * Client Portal Projects API
 */
export const clientPortalApi = {
  /**
   * List all projects for authenticated client
   */
  listProjects: (params?: { status?: string }) => {
    return apiClient.get<{ results: ClientProject[] }>('/api/clients/projects/', { params });
  },

  /**
   * Get project detail with tasks
   */
  getProject: (projectId: number) => {
    return apiClient.get<ClientProject>(`/api/clients/projects/${projectId}/`);
  },

  /**
   * Get tasks for a specific project
   */
  getProjectTasks: (projectId: number) => {
    return apiClient.get<ClientTask[]>(`/api/clients/projects/${projectId}/tasks/`);
  },

  /**
   * List comments (optionally filtered by task)
   */
  listComments: (params?: { task_id?: number }) => {
    return apiClient.get<{ results: ClientComment[] }>('/api/clients/comments/', { params });
  },

  /**
   * Create a new comment on a task
   */
  createComment: (data: CreateCommentData) => {
    return apiClient.post<ClientComment>('/api/clients/comments/', data);
  },

  /**
   * Mark a comment as read (firm users only)
   */
  markCommentAsRead: (commentId: number) => {
    return apiClient.post<{ status: string; comment: ClientComment }>(
      `/api/clients/comments/${commentId}/mark_as_read/`
    );
  },

  /**
   * Get unread comments (firm users only)
   */
  getUnreadComments: () => {
    return apiClient.get<ClientComment[]>('/api/clients/comments/unread/');
  },
};

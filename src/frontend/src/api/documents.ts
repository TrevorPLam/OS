import apiClient from './client'

export interface Document {
  id: number
  folder: number | null
  client: number
  project: number | null
  name: string
  description: string
  visibility: 'internal' | 'client_visible'
  file_type: string
  file_size_bytes: number
  s3_key?: string
  s3_bucket?: string
  current_version: number
  uploaded_by: number
  created_at: string
  updated_at: string
}

export interface Folder {
  id: number
  name: string
  client: number | null
  project: number | null
  parent: number | null
  visibility: 'internal' | 'client_visible'
  created_by: number
  created_at: string
  updated_at: string
}

export const documentsApi = {
  getDocuments: async (params?: { client?: number; project?: number; folder?: number }): Promise<Document[]> => {
    const response = await apiClient.get('/documents/documents/', { params })
    return response.data.results || response.data
  },

  getDocument: async (id: number): Promise<Document> => {
    const response = await apiClient.get(`/documents/documents/${id}/`)
    return response.data
  },

  uploadDocument: async (formData: FormData): Promise<Document> => {
    const response = await apiClient.post('/documents/documents/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  downloadDocument: async (id: number): Promise<{ download_url: string; expires_in: number }> => {
    const response = await apiClient.get(`/documents/documents/${id}/download/`)
    return response.data
  },

  deleteDocument: async (id: number): Promise<void> => {
    await apiClient.delete(`/documents/documents/${id}/`)
  },

  getFolders: async (params?: { client?: number; project?: number }): Promise<Folder[]> => {
    const response = await apiClient.get('/documents/folders/', { params })
    return response.data.results || response.data
  },

  createFolder: async (folder: Partial<Folder>): Promise<Folder> => {
    const response = await apiClient.post('/documents/folders/', folder)
    return response.data
  },

  deleteFolder: async (id: number): Promise<void> => {
    await apiClient.delete(`/documents/folders/${id}/`)
  },
}

import React, { useCallback, useEffect, useState } from 'react'
import { useClients } from '../api/clients'
import { documentsApi, Document, Folder } from '../api/documents'
import { useConfirmDialog } from '../components/ConfirmDialog'
import ErrorDisplay from '../components/ErrorDisplay'
import './Documents.css'

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [folders, setFolders] = useState<Folder[]>([])
  const { data: clients = [], isLoading: clientsLoading } = useClients()
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showFolderModal, setShowFolderModal] = useState(false)
  const [selectedClient, setSelectedClient] = useState<number | null>(null)
  const [documentToDelete, setDocumentToDelete] = useState<number | null>(null)

  const deleteDialog = useConfirmDialog({
    title: 'Delete Document',
    message: 'Are you sure you want to delete this document? This action cannot be undone.',
    variant: 'danger',
    confirmText: 'Delete',
    onConfirm: async () => {
      if (documentToDelete === null) return
      try {
        setError(null)
        await documentsApi.deleteDocument(documentToDelete)
        await loadData()
      } catch (err) {
        setError(resolveDocumentsError(err) || 'Delete failed')
      } finally {
        setDocumentToDelete(null)
      }
    },
  })

  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    client: 0,
    folder: null as number | null,
    name: '',
    description: '',
    visibility: 'internal' as 'internal' | 'client_visible',
  })

  const [folderForm, setFolderForm] = useState({
    name: '',
    client: 0,
    visibility: 'internal' as 'internal' | 'client_visible',
  })

  // Normalize API error payloads for consistent UI messaging.
  const resolveDocumentsError = (error: unknown) => {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as { response?: { data?: { error?: { message?: string } } } }).response
      return response?.data?.error?.message
    }
    if (error instanceof Error) {
      return error.message
    }
    return undefined
  }

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [docsData, foldersData] = await Promise.all([
        documentsApi.getDocuments(selectedClient ? { client: selectedClient } : {}),
        documentsApi.getFolders(selectedClient ? { client: selectedClient } : {}),
      ])
      setDocuments(docsData)
      setFolders(foldersData)
    } catch (error) {
      setError(resolveDocumentsError(error) || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }, [selectedClient])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadForm({
        ...uploadForm,
        file,
        name: uploadForm.name || file.name,
      })
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadForm.file || !uploadForm.client) {
      setError('Please select a file and client')
      return
    }

    try {
      setUploading(true)
      setError(null)

      const formData = new FormData()
      formData.append('file', uploadForm.file)
      formData.append('client', uploadForm.client.toString())
      formData.append('name', uploadForm.name)
      formData.append('description', uploadForm.description)
      formData.append('visibility', uploadForm.visibility)
      if (uploadForm.folder) {
        formData.append('folder', uploadForm.folder.toString())
      }

      await documentsApi.uploadDocument(formData)
      await loadData()
      resetUploadForm()
      setShowUploadModal(false)
    } catch (error) {
      setError(resolveDocumentsError(error) || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setError(null)
      await documentsApi.createFolder(folderForm)
      await loadData()
      resetFolderForm()
      setShowFolderModal(false)
    } catch (error) {
      setError(resolveDocumentsError(error) || 'Failed to create folder')
    }
  }

  const handleDownload = async (doc: Document) => {
    try {
      setError(null)
      const { download_url } = await documentsApi.downloadDocument(doc.id)
      window.open(download_url, '_blank')
    } catch (error) {
      setError(resolveDocumentsError(error) || 'Download failed')
    }
  }

  const handleDelete = (id: number) => {
    setDocumentToDelete(id)
    deleteDialog.show()
  }

  const resetUploadForm = () => {
    setUploadForm({
      file: null,
      client: clients.length > 0 ? clients[0].id : 0,
      folder: null,
      name: '',
      description: '',
      visibility: 'internal',
    })
  }

  const resetFolderForm = () => {
    setFolderForm({
      name: '',
      client: clients.length > 0 ? clients[0].id : 0,
      visibility: 'internal',
    })
  }

  const openUploadModal = () => {
    resetUploadForm()
    setShowUploadModal(true)
  }

  const openFolderModal = () => {
    resetFolderForm()
    setShowFolderModal(true)
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getClientName = (clientId: number) => {
    const client = clients.find((c) => c.id === clientId)
    return client ? client.company_name : 'Unknown'
  }

  if (loading || clientsLoading) {
    return <div className="loading">Loading documents...</div>
  }

  return (
    <div className="documents-page">
      <div className="page-header">
        <div>
          <h1>Documents</h1>
          <p className="subtitle">Manage client documents and files</p>
        </div>
        <div className="header-actions">
          <button onClick={openFolderModal} className="btn btn-secondary">
            + New Folder
          </button>
          <button onClick={openUploadModal} className="btn btn-primary">
            📤 Upload Document
          </button>
        </div>
      </div>

      {error && (
        <ErrorDisplay
          error={error}
          variant="banner"
          onDismiss={() => setError(null)}
        />
      )}

      <div className="filters">
        <label htmlFor="client-filter">Filter by Client:</label>
        <select
          id="client-filter"
          value={selectedClient || ''}
          onChange={(e) => setSelectedClient(e.target.value ? parseInt(e.target.value) : null)}
        >
          <option value="">All Clients</option>
          {clients.map((client) => (
            <option key={client.id} value={client.id}>
              {client.company_name}
            </option>
          ))}
        </select>
      </div>

      {folders.length > 0 && (
        <div className="folders-section">
          <h2>Folders</h2>
          <div className="folders-grid">
            {folders.map((folder) => (
              <div key={folder.id} className="folder-card">
                <div className="folder-icon">📁</div>
                <div className="folder-info">
                  <h3>{folder.name}</h3>
                  <p>
                    {folder.client ? getClientName(folder.client) : 'No client'} •{' '}
                    {folder.visibility === 'client_visible' ? 'Shared' : 'Internal'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="documents-section">
        <h2>Documents ({documents.length})</h2>
        {documents.length === 0 ? (
          <div className="empty-state">
            <p>No documents found. Upload your first document to get started.</p>
          </div>
        ) : (
          <div className="documents-table">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Client</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Visibility</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <div className="doc-name">
                        <span className="doc-icon">📄</span>
                        <div>
                          <div className="name">{doc.name}</div>
                          {doc.description && <div className="description">{doc.description}</div>}
                        </div>
                      </div>
                    </td>
                    <td>{getClientName(doc.client)}</td>
                    <td>
                      <span className="file-type">{doc.file_type.split('/')[1] || 'file'}</span>
                    </td>
                    <td>{formatFileSize(doc.file_size_bytes)}</td>
                    <td>
                      <span className={`visibility-badge ${doc.visibility}`}>
                        {doc.visibility === 'client_visible' ? '👁️ Shared' : '🔒 Internal'}
                      </span>
                    </td>
                    <td>{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td>
                      <div className="actions">
                        <button onClick={() => handleDownload(doc)} className="btn-text">
                          Download
                        </button>
                        <button onClick={() => handleDelete(doc.id)} className="btn-text text-danger">
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Upload Document</h2>
              <button className="modal-close" onClick={() => setShowUploadModal(false)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleUpload} className="upload-form">
              <div className="form-group">
                <label htmlFor="file">File *</label>
                <input
                  id="file"
                  type="file"
                  onChange={handleFileSelect}
                  required
                  className="file-input"
                />
                {uploadForm.file && (
                  <div className="file-selected">
                    📎 {uploadForm.file.name} ({formatFileSize(uploadForm.file.size)})
                  </div>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="upload-client">Client *</label>
                <select
                  id="upload-client"
                  value={uploadForm.client}
                  onChange={(e) => setUploadForm({ ...uploadForm, client: parseInt(e.target.value) })}
                  required
                >
                  <option value={0}>Select Client</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.company_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="upload-folder">Folder (Optional)</label>
                <select
                  id="upload-folder"
                  value={uploadForm.folder || ''}
                  onChange={(e) =>
                    setUploadForm({ ...uploadForm, folder: e.target.value ? parseInt(e.target.value) : null })
                  }
                >
                  <option value="">No Folder</option>
                  {folders
                    .filter((f) => !uploadForm.client || f.client === uploadForm.client)
                    .map((folder) => (
                      <option key={folder.id} value={folder.id}>
                        {folder.name}
                      </option>
                    ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="upload-name">Document Name *</label>
                <input
                  id="upload-name"
                  type="text"
                  value={uploadForm.name}
                  onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="upload-description">Description</label>
                <textarea
                  id="upload-description"
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label htmlFor="upload-visibility">Visibility</label>
                <select
                  id="upload-visibility"
                  value={uploadForm.visibility}
                  onChange={(e) =>
                    setUploadForm({ ...uploadForm, visibility: e.target.value as 'internal' | 'client_visible' })
                  }
                >
                  <option value="internal">Internal Only</option>
                  <option value="client_visible">Shared with Client</option>
                </select>
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowUploadModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={uploading} className="btn btn-primary">
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showFolderModal && (
        <div className="modal-overlay" onClick={() => setShowFolderModal(false)}>
          <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create Folder</h2>
              <button className="modal-close" onClick={() => setShowFolderModal(false)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateFolder}>
              <div className="form-group">
                <label htmlFor="folder-name">Folder Name *</label>
                <input
                  id="folder-name"
                  type="text"
                  value={folderForm.name}
                  onChange={(e) => setFolderForm({ ...folderForm, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="folder-client">Client *</label>
                <select
                  id="folder-client"
                  value={folderForm.client}
                  onChange={(e) => setFolderForm({ ...folderForm, client: parseInt(e.target.value) })}
                  required
                >
                  <option value={0}>Select Client</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.company_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="folder-visibility">Visibility</label>
                <select
                  id="folder-visibility"
                  value={folderForm.visibility}
                  onChange={(e) =>
                    setFolderForm({ ...folderForm, visibility: e.target.value as 'internal' | 'client_visible' })
                  }
                >
                  <option value="internal">Internal Only</option>
                  <option value="client_visible">Shared with Client</option>
                </select>
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowFolderModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <deleteDialog.ConfirmDialog />
    </div>
  )
}

export default Documents

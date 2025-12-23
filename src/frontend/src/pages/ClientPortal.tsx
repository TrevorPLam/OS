/**
 * Client Portal - Main dashboard for client users
 * Provides access to work, documents, invoices, messages, and analytics
 */
import React, { useState, useEffect } from 'react';
import { documentsApi } from '../api/documents';
import { clientPortalApi, ClientProject, ClientTask, CreateCommentData, ClientInvoice, InvoiceSummary, ClientChatThread, ClientMessage } from '../api/clientPortal';
import { LoadingSpinner } from '../components/LoadingSpinner';
import './ClientPortal.css';

interface Document {
  id: number;
  name: string;
  folder_name: string;
  file_type: string;
  file_size_bytes: number;
  created_at: string;
  description: string;
}

// Invoice and Chat interfaces now imported from clientPortal.ts

export const ClientPortal: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'work' | 'documents' | 'invoices' | 'messages' | 'analytics'>('work');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [projects, setProjects] = useState<ClientProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<ClientProject | null>(null);
  const [expandedTask, setExpandedTask] = useState<number | null>(null);
  const [commentText, setCommentText] = useState<{ [taskId: number]: string }>({});
  const [submittingComment, setSubmittingComment] = useState<number | null>(null);
  const [invoices, setInvoices] = useState<ClientInvoice[]>([]);
  const [invoiceSummary, setInvoiceSummary] = useState<InvoiceSummary | null>(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null);
  const [generatingPaymentLink, setGeneratingPaymentLink] = useState<number | null>(null);
  const [chatThread, setChatThread] = useState<ClientChatThread | null>(null);
  const [messages, setMessages] = useState<ClientMessage[]>([]);
  const [newMessage, setNewMessage] = useState<string>('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    activeProjects: 0,
    totalDocuments: 0,
    pendingInvoices: 0,
    unreadMessages: 0,
  });

  useEffect(() => {
    loadPortalData();
  }, []);

  const loadPortalData = async () => {
    try {
      setLoading(true);

      // Load projects
      const projectsResponse = await clientPortalApi.listProjects();
      const projectsList = projectsResponse.data.results || [];
      setProjects(projectsList);

      // Set first project as selected if available
      if (projectsList.length > 0 && !selectedProject) {
        setSelectedProject(projectsList[0]);
      }

      // Load client-visible documents only
      const docsResponse = await documentsApi.listDocuments({ visibility: 'client' });
      setDocuments(docsResponse.data.results || []);

      // Load invoices
      const invoicesResponse = await clientPortalApi.listInvoices();
      const invoicesList = invoicesResponse.data.results || [];
      setInvoices(invoicesList);

      // Load invoice summary
      const summaryResponse = await clientPortalApi.getInvoiceSummary();
      setInvoiceSummary(summaryResponse.data);

      // Calculate stats
      const activeProjectsCount = projectsList.filter(p => p.status === 'in_progress').length;
      const pendingInvoicesCount = invoicesList.filter(inv =>
        ['sent', 'partial', 'overdue'].includes(inv.status)
      ).length;

      // Load chat thread and messages
      try {
        const threadResponse = await clientPortalApi.getActiveThread();
        setChatThread(threadResponse.data);
        setMessages(threadResponse.data.recent_messages || []);

        // Count unread messages from firm
        const unreadCount = (threadResponse.data.recent_messages || []).filter(
          (msg: ClientMessage) => !msg.is_read && !msg.is_from_client
        ).length;

        setStats({
          activeProjects: activeProjectsCount,
          totalDocuments: docsResponse.data.results?.length || 0,
          pendingInvoices: pendingInvoicesCount,
          unreadMessages: unreadCount,
        });
      } catch (error) {
        console.error('Error loading chat:', error);
        setStats({
          activeProjects: activeProjectsCount,
          totalDocuments: docsResponse.data.results?.length || 0,
          pendingInvoices: pendingInvoicesCount,
          unreadMessages: 0,
        });
      }
    } catch (error) {
      console.error('Error loading portal data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadDocument = async (documentId: number) => {
    try {
      const response = await documentsApi.downloadDocument(documentId);
      window.open(response.data.download_url, '_blank');
    } catch (error) {
      console.error('Error downloading document:', error);
      alert('Failed to download document');
    }
  };

  const handleSubmitComment = async (taskId: number) => {
    const comment = commentText[taskId]?.trim();
    if (!comment) return;

    try {
      setSubmittingComment(taskId);
      const commentData: CreateCommentData = {
        task: taskId,
        comment: comment,
      };

      await clientPortalApi.createComment(commentData);

      // Clear comment input
      setCommentText({ ...commentText, [taskId]: '' });

      // Reload project to show new comment
      if (selectedProject) {
        const updatedProject = await clientPortalApi.getProject(selectedProject.id);
        setSelectedProject(updatedProject.data);

        // Update in projects list
        setProjects(projects.map(p =>
          p.id === selectedProject.id ? updatedProject.data : p
        ));
      }

      alert('Comment added successfully!');
    } catch (error) {
      console.error('Error submitting comment:', error);
      alert('Failed to add comment. Please try again.');
    } finally {
      setSubmittingComment(null);
    }
  };

  const handleGeneratePaymentLink = async (invoiceId: number) => {
    try {
      setGeneratingPaymentLink(invoiceId);
      const response = await clientPortalApi.generatePaymentLink(invoiceId);

      // Open payment link in new tab
      window.open(response.data.payment_url, '_blank');

      if (response.data.message) {
        alert(response.data.message);
      }
    } catch (error: any) {
      console.error('Error generating payment link:', error);
      const errorMessage = error.response?.data?.error || 'Failed to generate payment link. Please try again.';
      alert(errorMessage);
    } finally {
      setGeneratingPaymentLink(null);
    }
  };

  const handleSendMessage = async () => {
    const messageContent = newMessage.trim();
    if (!messageContent || !chatThread) return;

    try {
      setSendingMessage(true);
      await clientPortalApi.sendMessage({
        thread: chatThread.id,
        content: messageContent,
      });

      // Clear input
      setNewMessage('');

      // Reload messages
      const threadResponse = await clientPortalApi.getActiveThread();
      setMessages(threadResponse.data.recent_messages || []);
      setChatThread(threadResponse.data);
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setSendingMessage(false);
    }
  };

  // Auto-refresh messages every 5 seconds when on messages tab
  useEffect(() => {
    if (activeTab !== 'messages' || !chatThread) return;

    const refreshMessages = async () => {
      try {
        const threadResponse = await clientPortalApi.getActiveThread();
        setMessages(threadResponse.data.recent_messages || []);
        setChatThread(threadResponse.data);
      } catch (error) {
        console.error('Error refreshing messages:', error);
      }
    };

    const interval = setInterval(refreshMessages, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [activeTab, chatThread]);

  const getInvoiceStatusBadgeClass = (status: string): string => {
    const statusMap: { [key: string]: string } = {
      'draft': 'invoice-status-draft',
      'sent': 'invoice-status-sent',
      'paid': 'invoice-status-paid',
      'partial': 'invoice-status-partial',
      'overdue': 'invoice-status-overdue',
      'cancelled': 'invoice-status-cancelled',
    };
    return statusMap[status] || 'invoice-status-default';
  };

  const getStatusBadgeClass = (status: string): string => {
    const statusMap: { [key: string]: string } = {
      'todo': 'status-todo',
      'in_progress': 'status-in-progress',
      'review': 'status-review',
      'done': 'status-done',
      'planning': 'status-planning',
      'completed': 'status-completed',
      'on_hold': 'status-on-hold',
      'cancelled': 'status-cancelled',
    };
    return statusMap[status] || 'status-default';
  };

  const getPriorityBadgeClass = (priority: string): string => {
    const priorityMap: { [key: string]: string } = {
      'low': 'priority-low',
      'normal': 'priority-normal',
      'high': 'priority-high',
      'urgent': 'priority-urgent',
    };
    return priorityMap[priority] || 'priority-normal';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatDateTime = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return <LoadingSpinner message="Loading your portal..." />;
  }

  return (
    <div className="client-portal">
      <header className="portal-header">
        <h1>Client Portal</h1>
        <p className="portal-subtitle">Welcome back! Here's your project overview.</p>
      </header>

      {/* Stats Cards */}
      <div className="portal-stats">
        <div className="stat-card">
          <div className="stat-icon projects-icon">📋</div>
          <div className="stat-content">
            <h3>{stats.activeProjects}</h3>
            <p>Active Projects</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon documents-icon">📄</div>
          <div className="stat-content">
            <h3>{stats.totalDocuments}</h3>
            <p>Documents</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon invoices-icon">💰</div>
          <div className="stat-content">
            <h3>{stats.pendingInvoices}</h3>
            <p>Pending Invoices</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon messages-icon">💬</div>
          <div className="stat-content">
            <h3>{stats.unreadMessages}</h3>
            <p>Unread Messages</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="portal-tabs">
        <button
          className={`tab-button ${activeTab === 'work' ? 'active' : ''}`}
          onClick={() => setActiveTab('work')}
        >
          📋 Work
        </button>
        <button
          className={`tab-button ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          📄 Documents
        </button>
        <button
          className={`tab-button ${activeTab === 'invoices' ? 'active' : ''}`}
          onClick={() => setActiveTab('invoices')}
        >
          💰 Invoices
        </button>
        <button
          className={`tab-button ${activeTab === 'messages' ? 'active' : ''}`}
          onClick={() => setActiveTab('messages')}
        >
          💬 Messages
        </button>
        <button
          className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          📊 Analytics
        </button>
      </div>

      {/* Tab Content */}
      <div className="portal-content">
        {activeTab === 'work' && (
          <div className="work-tab">
            <h2>Your Projects & Tasks</h2>

            {projects.length === 0 ? (
              <p className="empty-state">No active projects yet.</p>
            ) : (
              <div className="work-layout">
                {/* Project Sidebar */}
                <div className="projects-sidebar">
                  <h3>Projects ({projects.length})</h3>
                  <div className="projects-list">
                    {projects.map((project) => (
                      <div
                        key={project.id}
                        className={`project-item ${selectedProject?.id === project.id ? 'active' : ''}`}
                        onClick={() => setSelectedProject(project)}
                      >
                        <div className="project-header">
                          <h4>{project.name}</h4>
                          <span className={`status-badge ${getStatusBadgeClass(project.status)}`}>
                            {project.status.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="project-code">{project.project_code}</p>
                        <div className="project-progress">
                          <div className="progress-bar">
                            <div
                              className="progress-fill"
                              style={{ width: `${project.progress_percentage}%` }}
                            />
                          </div>
                          <span className="progress-text">{project.progress_percentage}%</span>
                        </div>
                        <div className="project-stats-mini">
                          <span>📋 {project.tasks_summary.total} tasks</span>
                          <span>✅ {project.tasks_summary.done} done</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Project Detail & Tasks */}
                {selectedProject && (
                  <div className="project-detail">
                    <div className="project-info">
                      <div className="project-info-header">
                        <div>
                          <h3>{selectedProject.name}</h3>
                          <p className="project-description">{selectedProject.description}</p>
                        </div>
                        <span className={`status-badge ${getStatusBadgeClass(selectedProject.status)}`}>
                          {selectedProject.status.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="project-meta">
                        <div className="meta-item">
                          <strong>Project Manager:</strong> {selectedProject.project_manager_name}
                        </div>
                        <div className="meta-item">
                          <strong>Duration:</strong> {formatDate(selectedProject.start_date)} - {formatDate(selectedProject.end_date)}
                        </div>
                        <div className="meta-item">
                          <strong>Budget:</strong> ${parseFloat(selectedProject.budget).toLocaleString()}
                        </div>
                        <div className="meta-item">
                          <strong>Hours Logged:</strong> {selectedProject.total_hours_logged.toFixed(1)} hrs
                        </div>
                      </div>

                      <div className="tasks-summary-grid">
                        <div className="summary-card">
                          <div className="summary-count">{selectedProject.tasks_summary.todo}</div>
                          <div className="summary-label">To Do</div>
                        </div>
                        <div className="summary-card">
                          <div className="summary-count">{selectedProject.tasks_summary.in_progress}</div>
                          <div className="summary-label">In Progress</div>
                        </div>
                        <div className="summary-card">
                          <div className="summary-count">{selectedProject.tasks_summary.review}</div>
                          <div className="summary-label">Review</div>
                        </div>
                        <div className="summary-card">
                          <div className="summary-count">{selectedProject.tasks_summary.done}</div>
                          <div className="summary-label">Done</div>
                        </div>
                      </div>
                    </div>

                    {/* Tasks List */}
                    <div className="tasks-section">
                      <h4>Tasks ({selectedProject.tasks?.length || 0})</h4>

                      {!selectedProject.tasks || selectedProject.tasks.length === 0 ? (
                        <p className="empty-state">No tasks in this project yet.</p>
                      ) : (
                        <div className="tasks-list">
                          {selectedProject.tasks.map((task) => (
                            <div key={task.id} className="task-card">
                              <div
                                className="task-header"
                                onClick={() => setExpandedTask(expandedTask === task.id ? null : task.id)}
                              >
                                <div className="task-header-left">
                                  <h5>{task.title}</h5>
                                  <div className="task-badges">
                                    <span className={`status-badge ${getStatusBadgeClass(task.status)}`}>
                                      {task.status.replace('_', ' ')}
                                    </span>
                                    <span className={`priority-badge ${getPriorityBadgeClass(task.priority)}`}>
                                      {task.priority}
                                    </span>
                                  </div>
                                </div>
                                <div className="task-header-right">
                                  <div className="task-progress-mini">
                                    <div className="progress-circle" style={{
                                      background: `conic-gradient(#4CAF50 ${task.progress_percentage * 3.6}deg, #e0e0e0 0deg)`
                                    }}>
                                      <span>{task.progress_percentage}%</span>
                                    </div>
                                  </div>
                                  <button className="expand-btn">
                                    {expandedTask === task.id ? '▼' : '▶'}
                                  </button>
                                </div>
                              </div>

                              {expandedTask === task.id && (
                                <div className="task-details">
                                  <div className="task-description">
                                    <p>{task.description || 'No description provided.'}</p>
                                  </div>

                                  <div className="task-meta-grid">
                                    {task.assigned_to_name && (
                                      <div className="meta-item">
                                        <strong>Assigned to:</strong> {task.assigned_to_name}
                                      </div>
                                    )}
                                    {task.due_date && (
                                      <div className="meta-item">
                                        <strong>Due Date:</strong> {formatDate(task.due_date)}
                                      </div>
                                    )}
                                    {task.estimated_hours && (
                                      <div className="meta-item">
                                        <strong>Estimated Hours:</strong> {task.estimated_hours}
                                      </div>
                                    )}
                                    <div className="meta-item">
                                      <strong>Hours Logged:</strong> {task.hours_logged.toFixed(1)}
                                    </div>
                                  </div>

                                  {/* Comments Section */}
                                  <div className="task-comments">
                                    <h6>Comments ({task.comments?.length || 0})</h6>

                                    {task.comments && task.comments.length > 0 && (
                                      <div className="comments-list">
                                        {task.comments.map((comment) => (
                                          <div key={comment.id} className="comment">
                                            <div className="comment-header">
                                              <strong>{comment.author_name}</strong>
                                              <span className="comment-date">
                                                {formatDateTime(comment.created_at)}
                                              </span>
                                            </div>
                                            <p className="comment-text">{comment.comment}</p>
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Add Comment Form */}
                                    <div className="add-comment">
                                      <textarea
                                        value={commentText[task.id] || ''}
                                        onChange={(e) => setCommentText({
                                          ...commentText,
                                          [task.id]: e.target.value
                                        })}
                                        placeholder="Add a comment about this task..."
                                        rows={3}
                                        disabled={submittingComment === task.id}
                                      />
                                      <button
                                        onClick={() => handleSubmitComment(task.id)}
                                        disabled={!commentText[task.id]?.trim() || submittingComment === task.id}
                                        className="submit-comment-btn"
                                      >
                                        {submittingComment === task.id ? 'Submitting...' : 'Add Comment'}
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="documents-tab">
            <h2>Your Documents</h2>
            {documents.length === 0 ? (
              <p className="empty-state">No documents shared with you yet.</p>
            ) : (
              <div className="documents-grid">
                {documents.map((doc) => (
                  <div key={doc.id} className="document-card">
                    <div className="document-icon">
                      {doc.file_type.includes('pdf') ? '📕' :
                       doc.file_type.includes('image') ? '🖼️' :
                       doc.file_type.includes('word') ? '📘' : '📄'}
                    </div>
                    <div className="document-info">
                      <h4>{doc.name}</h4>
                      <p className="document-meta">
                        {doc.folder_name} • {formatFileSize(doc.file_size_bytes)} • {formatDate(doc.created_at)}
                      </p>
                      {doc.description && <p className="document-description">{doc.description}</p>}
                    </div>
                    <button
                      className="download-btn"
                      onClick={() => handleDownloadDocument(doc.id)}
                    >
                      Download
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'invoices' && (
          <div className="invoices-tab">
            <h2>Billing & Invoices</h2>

            {/* Invoice Summary Cards */}
            {invoiceSummary && (
              <div className="invoice-summary-cards">
                <div className="summary-card-billing">
                  <div className="card-icon">💵</div>
                  <div className="card-content">
                    <h3>${Number(invoiceSummary.total_billed).toLocaleString()}</h3>
                    <p>Total Billed</p>
                  </div>
                </div>
                <div className="summary-card-billing">
                  <div className="card-icon">✅</div>
                  <div className="card-content">
                    <h3>${Number(invoiceSummary.total_paid).toLocaleString()}</h3>
                    <p>Total Paid</p>
                  </div>
                </div>
                <div className="summary-card-billing outstanding">
                  <div className="card-icon">⏳</div>
                  <div className="card-content">
                    <h3>${Number(invoiceSummary.total_outstanding).toLocaleString()}</h3>
                    <p>Outstanding Balance</p>
                  </div>
                </div>
                {invoiceSummary.overdue_count > 0 && (
                  <div className="summary-card-billing overdue">
                    <div className="card-icon">⚠️</div>
                    <div className="card-content">
                      <h3>{invoiceSummary.overdue_count}</h3>
                      <p>Overdue Invoices</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Invoices List */}
            {invoices.length === 0 ? (
              <p className="empty-state">No invoices yet.</p>
            ) : (
              <div className="invoices-list">
                {invoices.map((invoice) => (
                  <div
                    key={invoice.id}
                    className={`invoice-card ${selectedInvoiceId === invoice.id ? 'expanded' : ''}`}
                  >
                    <div
                      className="invoice-header"
                      onClick={() => setSelectedInvoiceId(selectedInvoiceId === invoice.id ? null : invoice.id)}
                    >
                      <div className="invoice-header-left">
                        <h4>{invoice.invoice_number}</h4>
                        <p className="invoice-project">
                          {invoice.project_name ? (
                            <>
                              Project: {invoice.project_name}
                              {invoice.project_code && <span className="project-code-badge">{invoice.project_code}</span>}
                            </>
                          ) : (
                            'General Invoice'
                          )}
                        </p>
                      </div>
                      <div className="invoice-header-right">
                        <span className={`invoice-status-badge ${getInvoiceStatusBadgeClass(invoice.status)}`}>
                          {invoice.status.toUpperCase()}
                        </span>
                        <div className="invoice-amount">
                          <strong>${Number(invoice.total_amount).toLocaleString()}</strong>
                        </div>
                        <button className="expand-btn">
                          {selectedInvoiceId === invoice.id ? '▼' : '▶'}
                        </button>
                      </div>
                    </div>

                    {selectedInvoiceId === invoice.id && (
                      <div className="invoice-details">
                        {/* Invoice Metadata */}
                        <div className="invoice-meta-section">
                          <div className="invoice-meta-grid">
                            <div className="meta-item">
                              <strong>Issue Date:</strong> {formatDate(invoice.issue_date)}
                            </div>
                            <div className="meta-item">
                              <strong>Due Date:</strong> {formatDate(invoice.due_date)}
                              {invoice.days_until_due !== null && (
                                <span className={invoice.days_until_due < 0 ? 'overdue-text' : 'days-text'}>
                                  {invoice.days_until_due < 0
                                    ? ` (${Math.abs(invoice.days_until_due)} days overdue)`
                                    : ` (${invoice.days_until_due} days remaining)`
                                  }
                                </span>
                              )}
                            </div>
                            {invoice.paid_date && (
                              <div className="meta-item">
                                <strong>Paid Date:</strong> {formatDate(invoice.paid_date)}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Invoice Amounts */}
                        <div className="invoice-amounts-section">
                          <div className="amount-row">
                            <span>Subtotal:</span>
                            <span>${Number(invoice.subtotal).toLocaleString()}</span>
                          </div>
                          <div className="amount-row">
                            <span>Tax:</span>
                            <span>${Number(invoice.tax_amount).toLocaleString()}</span>
                          </div>
                          <div className="amount-row total">
                            <span>Total Amount:</span>
                            <span>${Number(invoice.total_amount).toLocaleString()}</span>
                          </div>
                          {Number(invoice.amount_paid) > 0 && (
                            <div className="amount-row paid">
                              <span>Amount Paid:</span>
                              <span>-${Number(invoice.amount_paid).toLocaleString()}</span>
                            </div>
                          )}
                          {Number(invoice.balance_due) > 0 && (
                            <div className="amount-row balance">
                              <span>Balance Due:</span>
                              <span className="balance-amount">${Number(invoice.balance_due).toLocaleString()}</span>
                            </div>
                          )}
                        </div>

                        {/* Line Items */}
                        {invoice.line_items && invoice.line_items.length > 0 && (
                          <div className="line-items-section">
                            <h5>Line Items</h5>
                            <table className="line-items-table">
                              <thead>
                                <tr>
                                  <th>Description</th>
                                  <th>Quantity</th>
                                  <th>Rate</th>
                                  <th>Amount</th>
                                </tr>
                              </thead>
                              <tbody>
                                {invoice.line_items.map((item, index) => (
                                  <tr key={index}>
                                    <td>{item.description}</td>
                                    <td>{item.quantity}</td>
                                    <td>${Number(item.rate).toLocaleString()}</td>
                                    <td>${Number(item.amount).toLocaleString()}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}

                        {/* Payment Actions */}
                        {invoice.can_pay_online && (
                          <div className="invoice-actions">
                            <button
                              className="pay-now-btn"
                              onClick={() => handleGeneratePaymentLink(invoice.id)}
                              disabled={generatingPaymentLink === invoice.id}
                            >
                              {generatingPaymentLink === invoice.id ? 'Processing...' : '💳 Pay Now'}
                            </button>
                            <p className="payment-note">
                              Secure payment via Stripe • ${Number(invoice.balance_due).toLocaleString()} due
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'messages' && (
          <div className="messages-tab">
            <h2>Team Chat</h2>

            {!chatThread ? (
              <p className="empty-state">Loading chat...</p>
            ) : (
              <div className="chat-container">
                {/* Chat Header */}
                <div className="chat-header">
                  <div className="chat-header-info">
                    <h3>Today's Conversation</h3>
                    <p className="chat-date">{new Date(chatThread.date).toLocaleDateString()}</p>
                  </div>
                  <div className="chat-stats">
                    <span className="message-count">{chatThread.message_count} messages</span>
                    {chatThread.last_message_at && (
                      <span className="last-activity">
                        Last activity: {new Date(chatThread.last_message_at).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Messages List */}
                <div className="chat-messages">
                  {messages.length === 0 ? (
                    <p className="empty-state">No messages yet. Start the conversation!</p>
                  ) : (
                    messages.map((message) => (
                      <div
                        key={message.id}
                        className={`message ${message.is_from_client ? 'message-client' : 'message-team'}`}
                      >
                        <div className="message-header">
                          <span className="message-sender">{message.sender_name}</span>
                          <span className="message-time">
                            {new Date(message.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="message-content">
                          {message.content}
                        </div>
                        {message.attachment_url && (
                          <div className="message-attachment">
                            <a href={message.attachment_url} target="_blank" rel="noopener noreferrer">
                              📎 {message.attachment_filename}
                            </a>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>

                {/* Message Input */}
                <div className="chat-input-container">
                  <textarea
                    className="chat-input"
                    placeholder="Type your message..."
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    rows={3}
                  />
                  <button
                    className="send-button"
                    onClick={handleSendMessage}
                    disabled={sendingMessage || !newMessage.trim()}
                  >
                    {sendingMessage ? 'Sending...' : '💬 Send'}
                  </button>
                  <p className="chat-hint">
                    Press Enter to send • Shift+Enter for new line • Messages refresh every 5 seconds
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="analytics-tab">
            <h2>Project Analytics</h2>
            <p className="coming-soon">Analytics dashboard coming soon. Track project progress, budget utilization, and milestones.</p>
          </div>
        )}
      </div>
    </div>
  );
};

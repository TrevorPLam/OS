/**
 * Client Portal - Main dashboard for client users
 * Provides access to work, documents, invoices, messages, and analytics
 */
import React, { useCallback, useEffect, useState } from 'react';
import { Document, portalDocumentsApi } from '../api/documents';
import {
  clientPortalApi,
  ClientProject,
  CreateCommentData,
  ClientInvoice,
  InvoiceSummary,
  ClientChatThread,
  ClientMessage,
  ClientProposal,
  ClientContract,
  ClientEngagement,
  PortalAppointment,
  PortalAppointmentSlot,
  PortalAppointmentType,
  PortalAccount,
  PortalProfile,
} from '../api/clientPortal';
import LoadingSpinner from '../components/LoadingSpinner';
import './ClientPortal.css';

const buildPortalPermissionSummary = (profile: PortalProfile) => [
  { label: 'Projects', enabled: profile.can_view_projects },
  { label: 'Invoices', enabled: profile.can_view_invoices },
  { label: 'Documents', enabled: profile.can_view_documents },
  { label: 'Uploads', enabled: profile.can_upload_documents },
  { label: 'Messages', enabled: profile.can_message_staff },
  { label: 'Appointments', enabled: profile.can_book_appointments },
];

const stringifyPreferences = (preferences: Record<string, unknown> | null) =>
  JSON.stringify(preferences ?? {}, null, 2);

const parsePreferences = (value: string) => {
  // Treat empty input as "no preferences" so users can reset without syntax errors.
  if (!value.trim()) {
    return {};
  }

  return JSON.parse(value) as Record<string, unknown>;
};

// Invoice and Chat interfaces now imported from clientPortal.ts

export const ClientPortal: React.FC = () => {
  const [activeTab, setActiveTab] = useState<
    'work' | 'documents' | 'invoices' | 'messages' | 'engagement' | 'appointments' | 'profile'
  >('work');
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
  const [proposals, setProposals] = useState<ClientProposal[]>([]);
  const [contracts, setContracts] = useState<ClientContract[]>([]);
  const [engagementHistory, setEngagementHistory] = useState<ClientEngagement[]>([]);
  const [selectedEngagementView, setSelectedEngagementView] = useState<'proposals' | 'contracts' | 'history'>('contracts');
  const [appointments, setAppointments] = useState<PortalAppointment[]>([]);
  const [appointmentTypes, setAppointmentTypes] = useState<PortalAppointmentType[]>([]);
  const [availableSlots, setAvailableSlots] = useState<PortalAppointmentSlot[]>([]);
  const [selectedAppointmentType, setSelectedAppointmentType] = useState<PortalAppointmentType | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<PortalAppointmentSlot | null>(null);
  const [appointmentNotes, setAppointmentNotes] = useState('');
  const [appointmentsLoading, setAppointmentsLoading] = useState(false);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [bookingAppointment, setBookingAppointment] = useState(false);
  const [appointmentsError, setAppointmentsError] = useState<string | null>(null);
  const [slotsError, setSlotsError] = useState<string | null>(null);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [profile, setProfile] = useState<PortalProfile | null>(null);
  const [profilePreferences, setProfilePreferences] = useState('');
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<PortalAccount[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [accountsError, setAccountsError] = useState<string | null>(null);
  const [currentAccountId, setCurrentAccountId] = useState<number | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [switchingAccount, setSwitchingAccount] = useState(false);
  const [accountSwitchMessage, setAccountSwitchMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    activeProjects: 0,
    totalDocuments: 0,
    pendingInvoices: 0,
    unreadMessages: 0,
  });

  // Centralize error extraction to keep portal messaging consistent without `any`.
  const resolvePortalError = (error: unknown) => {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as { response?: { data?: { error?: string } } }).response;
      return response?.data?.error;
    }
    if (error instanceof Error) {
      return error.message;
    }
    return undefined;
  };

  const loadAppointmentData = useCallback(async () => {
    try {
      setAppointmentsLoading(true);
      setAppointmentsError(null);

      const [appointmentsResponse, typesResponse] = await Promise.all([
        clientPortalApi.listAppointments(),
        clientPortalApi.listAppointmentTypes(),
      ]);

      setAppointments(appointmentsResponse.data.results || []);
      setAppointmentTypes(typesResponse.data || []);
    } catch (error) {
      console.error('Error loading appointments:', error);
      setAppointmentsError('Unable to load appointment options right now.');
    } finally {
      setAppointmentsLoading(false);
    }
  }, []);

  const loadProfileData = useCallback(async () => {
    try {
      setProfileLoading(true);
      setProfileError(null);

      const response = await clientPortalApi.getProfile();
      setProfile(response.data);
      setProfilePreferences(stringifyPreferences(response.data.notification_preferences ?? null));
    } catch (error) {
      console.error('Error loading profile:', error);
      setProfileError('Unable to load profile details right now.');
    } finally {
      setProfileLoading(false);
    }
  }, []);

  const loadAccountData = useCallback(async () => {
    try {
      setAccountsLoading(true);
      setAccountsError(null);

      const response = await clientPortalApi.listAccounts();
      setAccounts(response.data.accounts || []);
      setCurrentAccountId(response.data.current_account_id ?? null);
      setSelectedAccountId(response.data.current_account_id ?? null);
    } catch (error) {
      console.error('Error loading accounts:', error);
      setAccountsError('Unable to load account options right now.');
    } finally {
      setAccountsLoading(false);
    }
  }, []);

  const loadPortalData = useCallback(async () => {
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
      const docsResponse = await portalDocumentsApi.getDocuments({});
      setDocuments(docsResponse || []);

      // Load invoices
      const invoicesResponse = await clientPortalApi.listInvoices();
      const invoicesList = invoicesResponse.data.results || [];
      setInvoices(invoicesList);

      // Load invoice summary
      const summaryResponse = await clientPortalApi.getInvoiceSummary();
      setInvoiceSummary(summaryResponse.data);

      // Load engagement data
      const proposalsResponse = await clientPortalApi.listProposals();
      setProposals(proposalsResponse.data.results || []);

      const contractsResponse = await clientPortalApi.listContracts();
      setContracts(contractsResponse.data.results || []);

      const engagementResponse = await clientPortalApi.listEngagementHistory();
      setEngagementHistory(engagementResponse.data.results || []);

      await loadAppointmentData();
      await Promise.all([loadProfileData(), loadAccountData()]);

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
          totalDocuments: docsResponse.length || 0,
          pendingInvoices: pendingInvoicesCount,
          unreadMessages: unreadCount,
        });
      } catch (error) {
        console.error('Error loading chat:', error);
        setStats({
          activeProjects: activeProjectsCount,
          totalDocuments: docsResponse.length || 0,
          pendingInvoices: pendingInvoicesCount,
          unreadMessages: 0,
        });
      }
    } catch (error) {
      console.error('Error loading portal data:', error);
    } finally {
      setLoading(false);
    }
  }, [loadAccountData, loadAppointmentData, loadProfileData, selectedProject]);

  useEffect(() => {
    loadPortalData();
  }, [loadPortalData]);

  const buildAvailabilityRange = () => {
    // Keep a deterministic 14-day window so availability is predictable and fast for portal users.
    const startDate = new Date();
    const endDate = new Date();
    endDate.setDate(startDate.getDate() + 14);

    return {
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
    };
  };

  const handleSaveProfilePreferences = async () => {
    if (!profile) {
      setProfileError('Profile data is unavailable. Please refresh.');
      return;
    }

    // Fail fast on invalid JSON so we do not send malformed preferences to the API.
    let parsedPreferences: Record<string, unknown>;
    try {
      parsedPreferences = parsePreferences(profilePreferences);
    } catch (error) {
      setProfileError('Notification preferences must be valid JSON.');
      return;
    }

    try {
      setProfileSaving(true);
      setProfileError(null);

      const response = await clientPortalApi.updateProfile({
        notification_preferences: parsedPreferences,
      });

      setProfile(response.data);
      setProfilePreferences(stringifyPreferences(response.data.notification_preferences ?? null));
    } catch (error) {
      console.error('Error saving profile preferences:', error);
      setProfileError('Unable to save profile changes right now.');
    } finally {
      setProfileSaving(false);
    }
  };

  const handleSwitchAccount = async () => {
    if (!selectedAccountId) {
      setAccountsError('Select an account to switch.');
      return;
    }

    // Short-circuit when the user selects the already active account.
    if (selectedAccountId === currentAccountId) {
      setAccountSwitchMessage('You are already viewing this account.');
      return;
    }

    try {
      setSwitchingAccount(true);
      setAccountsError(null);
      setAccountSwitchMessage(null);

      await clientPortalApi.switchAccount(selectedAccountId);
      setCurrentAccountId(selectedAccountId);
      setAccountSwitchMessage('Account switched successfully.');

      // Refresh portal data to reflect the newly active account scope.
      await loadPortalData();
    } catch (error) {
      console.error('Error switching account:', error);
      setAccountsError('Unable to switch accounts right now.');
    } finally {
      setSwitchingAccount(false);
    }
  };

  const handleSelectAppointmentType = (type: PortalAppointmentType) => {
    // Reset slots when switching types so users never book against stale availability.
    setSelectedAppointmentType(type);
    setAvailableSlots([]);
    setSelectedSlot(null);
    setSlotsError(null);
    setBookingError(null);
  };

  const handleLoadSlots = async () => {
    if (!selectedAppointmentType) {
      setSlotsError('Select an appointment type to see available times.');
      return;
    }

    try {
      setSlotsLoading(true);
      setSlotsError(null);

      const { startDate, endDate } = buildAvailabilityRange();
      const response = await clientPortalApi.listAvailableAppointmentSlots({
        appointment_type_id: selectedAppointmentType.id,
        start_date: startDate,
        end_date: endDate,
      });

      setAvailableSlots(response.data.slots || []);
    } catch (error) {
      console.error('Error loading appointment slots:', error);
      setSlotsError('Unable to load appointment times. Please try again.');
    } finally {
      setSlotsLoading(false);
    }
  };

  const handleBookAppointment = async () => {
    if (!selectedAppointmentType || !selectedSlot) {
      setBookingError('Pick a type and time before booking.');
      return;
    }

    try {
      setBookingAppointment(true);
      setBookingError(null);

      await clientPortalApi.bookAppointment({
        appointment_type_id: selectedAppointmentType.id,
        start_time: selectedSlot.start_time,
        notes: appointmentNotes.trim() || undefined,
      });

      setAppointmentNotes('');
      setSelectedSlot(null);
      await loadAppointmentData();
      alert('Appointment booked successfully!');
    } catch (error) {
      console.error('Error booking appointment:', error);
      setBookingError('Unable to book this appointment. Please try another time.');
    } finally {
      setBookingAppointment(false);
    }
  };

  const handleCancelAppointment = async (appointmentId: number) => {
    try {
      await clientPortalApi.cancelAppointment(appointmentId);
      await loadAppointmentData();
    } catch (error) {
      console.error('Error cancelling appointment:', error);
      alert('Unable to cancel appointment right now.');
    }
  };

  const handleDownloadDocument = async (documentId: number) => {
    try {
      const response = await portalDocumentsApi.downloadDocument(documentId);
      window.open(response.download_url, '_blank');
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
    } catch (error) {
      console.error('Error generating payment link:', error);
      const errorMessage =
        resolvePortalError(error) || 'Failed to generate payment link. Please try again.';
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

  const formatSlotLabel = (slot: PortalAppointmentSlot): string => {
    const start = new Date(slot.start_time).toLocaleString();
    const end = new Date(slot.end_time).toLocaleTimeString();
    return `${start} → ${end}`;
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
          className={`tab-button ${activeTab === 'engagement' ? 'active' : ''}`}
          onClick={() => setActiveTab('engagement')}
        >
          📋 Engagement
        </button>
        <button
          className={`tab-button ${activeTab === 'appointments' ? 'active' : ''}`}
          onClick={() => setActiveTab('appointments')}
        >
          🗓️ Appointments
        </button>
        <button
          className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          👤 Profile
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

        {activeTab === 'engagement' && (
          <div className="engagement-tab">
            <h2>Contracts & Engagements</h2>

            {/* Sub-navigation */}
            <div className="engagement-sub-nav">
              <button
                className={`sub-nav-btn ${selectedEngagementView === 'contracts' ? 'active' : ''}`}
                onClick={() => setSelectedEngagementView('contracts')}
              >
                Active Contracts
              </button>
              <button
                className={`sub-nav-btn ${selectedEngagementView === 'proposals' ? 'active' : ''}`}
                onClick={() => setSelectedEngagementView('proposals')}
              >
                Proposals
              </button>
              <button
                className={`sub-nav-btn ${selectedEngagementView === 'history' ? 'active' : ''}`}
                onClick={() => setSelectedEngagementView('history')}
              >
                Engagement History
              </button>
            </div>

            {/* Contracts View */}
            {selectedEngagementView === 'contracts' && (
              <div className="contracts-section">
                <h3>Your Contracts</h3>
                {contracts.length === 0 ? (
                  <p className="empty-state">No contracts yet.</p>
                ) : (
                  <div className="contracts-list">
                    {contracts.map((contract) => (
                      <div key={contract.id} className="contract-card">
                        <div className="contract-header">
                          <div>
                            <h4>{contract.title}</h4>
                            <p className="contract-number">{contract.contract_number}</p>
                          </div>
                          <span className={`status-badge contract-status-${contract.status}`}>
                            {contract.status_display}
                          </span>
                        </div>
                        <div className="contract-body">
                          <p className="contract-description">{contract.description}</p>
                          <div className="contract-meta">
                            <div className="meta-item">
                              <strong>Value:</strong> ${Number(contract.total_value).toLocaleString()} {contract.currency}
                            </div>
                            <div className="meta-item">
                              <strong>Period:</strong> {formatDate(contract.start_date)} - {formatDate(contract.end_date)}
                            </div>
                            <div className="meta-item">
                              <strong>Payment Terms:</strong> {contract.payment_terms_display}
                            </div>
                            {contract.signed_date && (
                              <div className="meta-item">
                                <strong>Signed:</strong> {formatDate(contract.signed_date)}
                              </div>
                            )}
                            {contract.days_remaining !== null && contract.is_active && (
                              <div className="meta-item">
                                <strong>Days Remaining:</strong>
                                <span className={contract.days_remaining < 30 ? 'expiring-soon' : ''}>
                                  {contract.days_remaining} days
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                        {contract.contract_file_url && (
                          <div className="contract-actions">
                            <button
                              className="download-contract-btn"
                              onClick={() => window.open(contract.contract_file_url, '_blank')}
                            >
                              📄 Download Contract
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Proposals View */}
            {selectedEngagementView === 'proposals' && (
              <div className="proposals-section">
                <h3>Your Proposals</h3>
                {proposals.length === 0 ? (
                  <p className="empty-state">No proposals yet.</p>
                ) : (
                  <div className="proposals-list">
                    {proposals.map((proposal) => (
                      <div key={proposal.id} className="proposal-card">
                        <div className="proposal-header">
                          <div>
                            <h4>{proposal.title}</h4>
                            <p className="proposal-number">{proposal.proposal_number}</p>
                            <p className="proposal-type">{proposal.type_display}</p>
                          </div>
                          <span className={`status-badge proposal-status-${proposal.status}`}>
                            {proposal.status_display}
                          </span>
                        </div>
                        <div className="proposal-body">
                          <p className="proposal-description">{proposal.description}</p>
                          <div className="proposal-meta">
                            <div className="meta-item">
                              <strong>Value:</strong> ${Number(proposal.total_value).toLocaleString()} {proposal.currency}
                            </div>
                            <div className="meta-item">
                              <strong>Valid Until:</strong> {formatDate(proposal.valid_until)}
                              {proposal.days_until_expiry !== null && (
                                <span className={proposal.is_expired ? 'expired-text' : proposal.days_until_expiry < 7 ? 'expiring-soon' : ''}>
                                  {proposal.is_expired
                                    ? ' (Expired)'
                                    : ` (${proposal.days_until_expiry} days remaining)`
                                  }
                                </span>
                              )}
                            </div>
                            {proposal.estimated_start_date && proposal.estimated_end_date && (
                              <div className="meta-item">
                                <strong>Estimated Duration:</strong> {formatDate(proposal.estimated_start_date)} - {formatDate(proposal.estimated_end_date)}
                              </div>
                            )}
                            {proposal.sent_at && (
                              <div className="meta-item">
                                <strong>Sent:</strong> {formatDateTime(proposal.sent_at)}
                              </div>
                            )}
                            {proposal.accepted_at && (
                              <div className="meta-item">
                                <strong>Accepted:</strong> {formatDateTime(proposal.accepted_at)}
                              </div>
                            )}
                          </div>
                        </div>
                        {proposal.status === 'sent' && !proposal.is_expired && (
                          <div className="proposal-actions">
                            <button
                              className="accept-proposal-btn"
                              onClick={() => alert('E-signature integration pending. This would trigger DocuSign/HelloSign workflow.')}
                            >
                              ✍️ Review & Sign
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Engagement History View */}
            {selectedEngagementView === 'history' && (
              <div className="engagement-history-section">
                <h3>Engagement History</h3>
                {engagementHistory.length === 0 ? (
                  <p className="empty-state">No engagement history yet.</p>
                ) : (
                  <div className="engagement-timeline">
                    {engagementHistory.map((engagement) => (
                      <div key={engagement.id} className="engagement-card">
                        <div className="engagement-version-badge">
                          Version {engagement.version}
                        </div>
                        <div className="engagement-header">
                          <h4>{engagement.contract.title}</h4>
                          <span className={`status-badge engagement-status-${engagement.status}`}>
                            {engagement.status_display}
                          </span>
                        </div>
                        <div className="engagement-body">
                          <div className="engagement-meta">
                            <div className="meta-item">
                              <strong>Contract:</strong> {engagement.contract.contract_number}
                            </div>
                            <div className="meta-item">
                              <strong>Period:</strong> {formatDate(engagement.start_date)} - {formatDate(engagement.end_date)}
                            </div>
                            {engagement.actual_end_date && (
                              <div className="meta-item">
                                <strong>Actual End:</strong> {formatDate(engagement.actual_end_date)}
                              </div>
                            )}
                            <div className="meta-item">
                              <strong>Value:</strong> ${Number(engagement.contract.total_value).toLocaleString()} {engagement.contract.currency}
                            </div>
                          </div>
                          {engagement.has_parent && (
                            <p className="engagement-note">🔄 This is a renewal of a previous engagement</p>
                          )}
                          {engagement.has_renewals && (
                            <p className="engagement-note">✅ This engagement has been renewed</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'appointments' && (
          <div className="appointments-tab">
            <h2>Appointments</h2>

            {appointmentsError && (
              <p className="error-state">{appointmentsError}</p>
            )}

            <div className="appointments-layout">
              <div className="appointments-list">
                <h3>Upcoming Appointments</h3>
                {appointmentsLoading ? (
                  <p className="loading-state">Loading appointments...</p>
                ) : appointments.length === 0 ? (
                  <p className="empty-state">No upcoming appointments yet.</p>
                ) : (
                  <div className="appointment-cards">
                    {appointments.map((appointment) => (
                      <div key={appointment.id} className="appointment-card">
                        <div className="appointment-card-header">
                          <div>
                            <h4>{appointment.appointment_type_name}</h4>
                            <p className="appointment-meta">
                              {formatDateTime(appointment.start_time)}
                            </p>
                          </div>
                          <span className={`appointment-status appointment-status-${appointment.status}`}>
                            {appointment.status.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="appointment-details">
                          {appointment.staff_name && (
                            <p><strong>Staff:</strong> {appointment.staff_name}</p>
                          )}
                          <p><strong>Location:</strong> {appointment.location_mode}</p>
                        </div>
                        {appointment.status === 'scheduled' && (
                          <button
                            className="cancel-appointment-btn"
                            onClick={() => handleCancelAppointment(appointment.id)}
                          >
                            Cancel appointment
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="appointments-booking">
                <h3>Book a New Appointment</h3>

                {appointmentTypes.length === 0 ? (
                  <p className="empty-state">No appointment types available.</p>
                ) : (
                  <div className="appointment-types">
                    {appointmentTypes.map((type) => (
                      <button
                        key={type.id}
                        className={`appointment-type-card ${selectedAppointmentType?.id === type.id ? 'active' : ''}`}
                        onClick={() => handleSelectAppointmentType(type)}
                      >
                        <h4>{type.name}</h4>
                        <p>{type.description}</p>
                        <span>{type.duration_minutes} min • {type.location_mode}</span>
                      </button>
                    ))}
                  </div>
                )}

                {selectedAppointmentType && (
                  <div className="appointment-availability">
                    <div className="availability-header">
                      <h4>Available Times</h4>
                      <button
                        className="load-slots-btn"
                        onClick={handleLoadSlots}
                        disabled={slotsLoading}
                      >
                        {slotsLoading ? 'Loading...' : 'Check availability'}
                      </button>
                    </div>

                    {slotsError && <p className="error-state">{slotsError}</p>}

                    {availableSlots.length === 0 && !slotsLoading ? (
                      <p className="empty-state">No available times yet. Try another type or check back soon.</p>
                    ) : (
                      <div className="appointment-slots">
                        {availableSlots.map((slot) => (
                          <button
                            key={slot.start_time}
                            className={`slot-btn ${selectedSlot?.start_time === slot.start_time ? 'active' : ''}`}
                            onClick={() => {
                              setSelectedSlot(slot);
                              setBookingError(null);
                            }}
                          >
                            {formatSlotLabel(slot)}
                          </button>
                        ))}
                      </div>
                    )}

                    <div className="appointment-notes">
                      <label htmlFor="appointment-notes">Notes (optional)</label>
                      <textarea
                        id="appointment-notes"
                        placeholder="Share any context or prep notes with your team."
                        value={appointmentNotes}
                        onChange={(event) => setAppointmentNotes(event.target.value)}
                        rows={3}
                      />
                    </div>

                    {bookingError && <p className="error-state">{bookingError}</p>}

                    <button
                      className="book-appointment-btn"
                      onClick={handleBookAppointment}
                      disabled={bookingAppointment || !selectedSlot}
                    >
                      {bookingAppointment ? 'Booking...' : 'Book appointment'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'profile' && (
          <div className="profile-tab">
            <h2>Profile & Accounts</h2>

            {profileError && <p className="error-state">{profileError}</p>}

            <div className="profile-grid">
              <section className="profile-card">
                <h3>Your Profile</h3>
                {profileLoading ? (
                  <p className="loading-state">Loading profile...</p>
                ) : profile ? (
                  <>
                    <div className="profile-detail">
                      <span className="profile-label">Name</span>
                      <span>{profile.full_name}</span>
                    </div>
                    <div className="profile-detail">
                      <span className="profile-label">Email</span>
                      <span>{profile.email}</span>
                    </div>
                    <div className="profile-detail">
                      <span className="profile-label">Account</span>
                      <span>{profile.client_name}</span>
                    </div>
                    <div className="profile-permissions">
                      <span className="profile-label">Permissions</span>
                      <div className="profile-permission-list">
                        {buildPortalPermissionSummary(profile).map((permission) => (
                          <span
                            key={permission.label}
                            className={`permission-pill ${permission.enabled ? 'enabled' : 'disabled'}`}
                          >
                            {permission.label}
                          </span>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="empty-state">Profile details are unavailable.</p>
                )}
              </section>

              <section className="profile-card">
                <h3>Notification Preferences</h3>
                <p className="helper-text">
                  Update your notification preferences using JSON (for example, {`{"email": true}`}).
                </p>
                <textarea
                  className="profile-textarea"
                  aria-label="Notification preferences"
                  value={profilePreferences}
                  onChange={(event) => setProfilePreferences(event.target.value)}
                  rows={6}
                />
                <button
                  className="profile-save-btn"
                  onClick={handleSaveProfilePreferences}
                  disabled={profileSaving || profileLoading}
                >
                  {profileSaving ? 'Saving...' : 'Save preferences'}
                </button>
              </section>

              <section className="profile-card">
                <h3>Account Switcher</h3>
                {accountsError && <p className="error-state">{accountsError}</p>}
                {accountSwitchMessage && <p className="success-state">{accountSwitchMessage}</p>}
                {accountsLoading ? (
                  <p className="loading-state">Loading accounts...</p>
                ) : accounts.length === 0 ? (
                  <p className="empty-state">No accounts available for switching.</p>
                ) : (
                  <div className="account-switcher">
                    <label htmlFor="account-switcher" className="profile-label">
                      Active account
                    </label>
                    <select
                      id="account-switcher"
                      value={selectedAccountId ?? ''}
                      onChange={(event) => {
                        const nextValue = event.target.value;
                        setSelectedAccountId(nextValue ? Number(nextValue) : null);
                        setAccountSwitchMessage(null);
                      }}
                    >
                      {accounts.map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.name}{account.account_number ? ` • ${account.account_number}` : ''}
                        </option>
                      ))}
                    </select>
                    <button
                      className="account-switch-btn"
                      onClick={handleSwitchAccount}
                      disabled={switchingAccount}
                    >
                      {switchingAccount ? 'Switching...' : 'Switch account'}
                    </button>
                    {currentAccountId && (
                      <p className="helper-text">
                        Current account ID: {currentAccountId}
                      </p>
                    )}
                  </div>
                )}
              </section>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

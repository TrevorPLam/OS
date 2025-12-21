/**
 * Client Portal - Main dashboard for client users
 * Provides access to documents, invoices, messages, and analytics
 */
import React, { useState, useEffect } from 'react';
import { documentsApi } from '../api/documents';
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

interface Invoice {
  id: number;
  invoice_number: string;
  total_amount: string;
  amount_paid: string;
  status: string;
  issue_date: string;
  due_date: string;
  balance_due: string;
}

interface Message {
  id: number;
  from_user: string;
  message: string;
  created_at: string;
  read: boolean;
}

export const ClientPortal: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'documents' | 'invoices' | 'messages' | 'analytics'>('documents');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    pendingInvoices: 0,
    unreadMessages: 0,
    totalSpent: 0
  });

  useEffect(() => {
    loadPortalData();
  }, []);

  const loadPortalData = async () => {
    try {
      setLoading(true);
      // Load client-visible documents only
      const docsResponse = await documentsApi.listDocuments({ visibility: 'client' });
      setDocuments(docsResponse.data.results || []);

      // TODO: Load invoices from finance API
      // TODO: Load messages from communications API

      // Calculate stats
      setStats({
        totalDocuments: docsResponse.data.results?.length || 0,
        pendingInvoices: 0,
        unreadMessages: 0,
        totalSpent: 0
      });
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

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
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
        <div className="stat-card">
          <div className="stat-icon spent-icon">📊</div>
          <div className="stat-content">
            <h3>${stats.totalSpent.toLocaleString()}</h3>
            <p>Total Spent</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="portal-tabs">
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
            <h2>Your Invoices</h2>
            <p className="coming-soon">Invoice viewing coming soon. You'll be able to view and pay invoices directly from this portal.</p>
          </div>
        )}

        {activeTab === 'messages' && (
          <div className="messages-tab">
            <h2>Messages</h2>
            <p className="coming-soon">Messaging feature coming soon. Direct communication with your consulting team.</p>
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

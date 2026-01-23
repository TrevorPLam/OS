/**
 * Communications Hub - Internal team chat, client messages, and email triage
 */
import React, { useState } from 'react';
import './Communications.css';

interface Message {
  id: number;
  from: string;
  to: string;
  subject: string;
  message: string;
  timestamp: string;
  read: boolean;
  type: 'team' | 'client' | 'email';
}

export const Communications: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'team' | 'client' | 'email'>('team');
  const [selectedConversation, setSelectedConversation] = useState<number | null>(null);
  const [messageText, setMessageText] = useState('');

  // Mock data - replace with WebSocket/API integration
  const [messages] = useState<Message[]>([
    {
      id: 1,
      from: 'Sarah Johnson',
      to: 'Team',
      subject: 'Project Update',
      message: 'Hey team, just finished the client presentation. It went really well!',
      timestamp: '2025-01-20T14:30:00',
      read: true,
      type: 'team'
    },
    {
      id: 2,
      from: 'Michael Torres',
      to: 'Team',
      subject: 'Sprint Planning',
      message: 'Can we schedule sprint planning for tomorrow morning?',
      timestamp: '2025-01-20T15:45:00',
      read: false,
      type: 'team'
    },
    {
      id: 3,
      from: 'client@acmecorp.com',
      to: 'You',
      subject: 'Question about deliverables',
      message: 'When can we expect the final report?',
      timestamp: '2025-01-20T16:00:00',
      read: false,
      type: 'client'
    }
  ]);

  const filteredMessages = messages.filter(m => m.type === activeTab);
  const unreadCount = (type: string) => messages.filter(m => m.type === type && !m.read).length;

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    // DEFERRED: WebSocket message sending - See TODO_ANALYSIS.md #6
    // Requires: Backend WebSocket server implementation (DOC-33.1)
    console.log('Sending message:', messageText);
    setMessageText('');
  };

  return (
    <div className="communications">
      <header className="comm-header">
        <div>
          <h1>Communications</h1>
          <p>Team chat, client messages, and email management</p>
        </div>
      </header>

      <div className="comm-container">
        {/* Sidebar with channels */}
        <div className="comm-sidebar">
          <div className="comm-tabs">
            <button
              className={`comm-tab ${activeTab === 'team' ? 'active' : ''}`}
              onClick={() => setActiveTab('team')}
            >
              <span className="tab-icon">👥</span>
              <span className="tab-label">Team Chat</span>
              {unreadCount('team') > 0 && (
                <span className="unread-badge">{unreadCount('team')}</span>
              )}
            </button>
            <button
              className={`comm-tab ${activeTab === 'client' ? 'active' : ''}`}
              onClick={() => setActiveTab('client')}
            >
              <span className="tab-icon">💬</span>
              <span className="tab-label">Client Messages</span>
              {unreadCount('client') > 0 && (
                <span className="unread-badge">{unreadCount('client')}</span>
              )}
            </button>
            <button
              className={`comm-tab ${activeTab === 'email' ? 'active' : ''}`}
              onClick={() => setActiveTab('email')}
            >
              <span className="tab-icon">📧</span>
              <span className="tab-label">Email Triage</span>
              {unreadCount('email') > 0 && (
                <span className="unread-badge">{unreadCount('email')}</span>
              )}
            </button>
          </div>

          <div className="channel-list">
            <h3>
              {activeTab === 'team' && 'Channels'}
              {activeTab === 'client' && 'Clients'}
              {activeTab === 'email' && 'Inbox'}
            </h3>
            <div className="channels">
              {activeTab === 'team' && (
                <>
                  <div className="channel-item active">
                    <span className="channel-icon">#</span>
                    <span className="channel-name">general</span>
                  </div>
                  <div className="channel-item">
                    <span className="channel-icon">#</span>
                    <span className="channel-name">projects</span>
                  </div>
                  <div className="channel-item">
                    <span className="channel-icon">#</span>
                    <span className="channel-name">random</span>
                  </div>
                </>
              )}
              {activeTab === 'client' && (
                <>
                  <div className="channel-item">
                    <span className="channel-icon">🏢</span>
                    <span className="channel-name">Acme Corp</span>
                    <span className="unread-dot"></span>
                  </div>
                  <div className="channel-item">
                    <span className="channel-icon">🏢</span>
                    <span className="channel-name">TechStart Inc</span>
                  </div>
                </>
              )}
              {activeTab === 'email' && (
                <p className="coming-soon-small">Email integration coming soon</p>
              )}
            </div>
          </div>
        </div>

        {/* Main chat area */}
        <div className="comm-main">
          {activeTab === 'team' && (
            <>
              <div className="chat-header">
                <h2># general</h2>
                <p>Team-wide announcements and discussions</p>
              </div>

              <div className="messages-container">
                {filteredMessages.map((msg) => (
                  <div key={msg.id} className="message-item">
                    <div className="message-avatar">
                      {msg.from.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div className="message-content">
                      <div className="message-header">
                        <strong>{msg.from}</strong>
                        <span className="message-time">
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="message-text">{msg.message}</div>
                    </div>
                  </div>
                ))}
              </div>

              <form className="message-input" onSubmit={handleSendMessage}>
                <input
                  type="text"
                  placeholder="Type a message..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                />
                <button type="submit" disabled={!messageText.trim()}>
                  Send
                </button>
              </form>
            </>
          )}

          {activeTab === 'client' && (
            <div className="feature-placeholder">
              <div className="placeholder-icon">💬</div>
              <h2>Client Messaging</h2>
              <p>Secure communication channel with your clients</p>
              <ul className="feature-list">
                <li>✓ Real-time messaging with client contacts</li>
                <li>✓ File sharing and attachments</li>
                <li>✓ Message history and search</li>
                <li>✓ Email notifications</li>
              </ul>
              <p className="coming-soon">Coming soon - Requires WebSocket backend integration</p>
            </div>
          )}

          {activeTab === 'email' && (
            <div className="feature-placeholder">
              <div className="placeholder-icon">📧</div>
              <h2>Email Triage</h2>
              <p>Centralized email management for the team</p>
              <ul className="feature-list">
                <li>✓ Shared team inbox</li>
                <li>✓ Email assignment and routing</li>
                <li>✓ Priority tagging</li>
                <li>✓ Response templates</li>
                <li>✓ Integration with Gmail/Outlook</li>
              </ul>
              <p className="coming-soon">Coming soon - Requires email API integration (IMAP/OAuth)</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

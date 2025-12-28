/**
 * Communications Hub - Internal team chat, client messages, and email triage
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
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

type WebSocketStatus = 'connecting' | 'open' | 'closed' | 'error';

const initialMessages: Message[] = [
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
];

const buildWebSocketUrl = () => {
  const envUrl = import.meta.env.VITE_WS_URL;
  if (envUrl) {
    return envUrl;
  }

  if (typeof window === 'undefined') {
    return 'ws://localhost:8000/ws/communications';
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/communications`;
};

export const Communications: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'team' | 'client' | 'email'>('team');
  const [selectedConversation, setSelectedConversation] = useState<number | null>(null);
  const [messageText, setMessageText] = useState('');
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [connectionStatus, setConnectionStatus] = useState<WebSocketStatus>('connecting');
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const wsUrl = useMemo(() => buildWebSocketUrl(), []);

  const filteredMessages = messages.filter(m => m.type === activeTab);
  const unreadCount = (type: string) => messages.filter(m => m.type === type && !m.read).length;

  useEffect(() => {
    setConnectionStatus('connecting');
    setConnectionError(null);

    let socket: WebSocket;

    try {
      socket = new WebSocket(wsUrl);
    } catch (error) {
      setConnectionStatus('error');
      setConnectionError('Unable to connect to messaging service.');
      return;
    }
    socketRef.current = socket;

    socket.onopen = () => {
      setConnectionStatus('open');
      setConnectionError(null);
    };

    socket.onerror = () => {
      setConnectionStatus('error');
      setConnectionError('Unable to connect to messaging service.');
    };

    socket.onclose = () => {
      setConnectionStatus('closed');
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as Message;
        if (payload && payload.message && payload.type) {
          setMessages((prev) => [...prev, payload]);
        }
      } catch (error) {
        setConnectionError('Received malformed message payload.');
      }
    };

    return () => {
      socket.close();
    };
  }, [wsUrl]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageText.trim()) {
      return;
    }

    if (connectionStatus !== 'open' || !socketRef.current) {
      setConnectionError('Messaging service is not connected yet.');
      return;
    }

    const outgoingMessage: Message = {
      id: Date.now(),
      from: 'You',
      to: activeTab === 'team' ? 'Team' : activeTab === 'client' ? 'Client' : 'Inbox',
      subject: activeTab === 'team' ? 'Team Chat' : activeTab === 'client' ? 'Client Message' : 'Email',
      message: messageText.trim(),
      timestamp: new Date().toISOString(),
      read: true,
      type: activeTab
    };

    try {
      socketRef.current.send(JSON.stringify(outgoingMessage));
      setMessages((prev) => [...prev, outgoingMessage]);
      setMessageText('');
      setConnectionError(null);
    } catch (error) {
      setConnectionError('Failed to send message. Please try again.');
    }
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
                  disabled={connectionStatus === 'connecting'}
                />
                <button type="submit" disabled={!messageText.trim() || connectionStatus !== 'open'}>
                  Send
                </button>
              </form>
              <div className={`connection-status ${connectionStatus}`}>
                {connectionStatus === 'connecting' && <span>Connecting to messaging service...</span>}
                {connectionStatus === 'error' && <span>{connectionError ?? 'Connection error.'}</span>}
                {connectionStatus === 'closed' && <span>Connection closed.</span>}
              </div>
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

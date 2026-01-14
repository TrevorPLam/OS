import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import './CommandCenter.css'

interface Module {
  id: string
  title: string
  icon: string
  content: React.ReactNode
}

const CommandCenter: React.FC = () => {
  const [currentModuleIndex, setCurrentModuleIndex] = useState(0)

  const modules: Module[] = [
    {
      id: 'crm',
      title: 'CRM',
      icon: '👥',
      content: (
        <div className="module-content">
          <h2>CRM Module</h2>
          <p>Manage clients, proposals, and contracts</p>
          <div className="module-links">
            <Link to="/clients">Clients</Link>
            <Link to="/proposals">Proposals</Link>
            <Link to="/contracts">Contracts</Link>
            <Link to="/crm/leads">Leads</Link>
            <Link to="/crm/prospects">Prospects</Link>
          </div>
        </div>
      )
    },
    {
      id: 'projects',
      title: 'Projects',
      icon: '📋',
      content: (
        <div className="module-content">
          <h2>Projects Module</h2>
          <p>Track projects, tasks, and time</p>
          <div className="module-links">
            <Link to="/projects">Projects</Link>
            <Link to="/time-tracking">Time Tracking</Link>
          </div>
        </div>
      )
    },
    {
      id: 'finance',
      title: 'Finance',
      icon: '💰',
      content: (
        <div className="module-content">
          <h2>Finance Module</h2>
          <p>Handle invoicing and accounting</p>
          <div className="module-links">
            <Link to="/invoices">Invoices</Link>
          </div>
        </div>
      )
    },
    {
      id: 'documents',
      title: 'Documents',
      icon: '📄',
      content: (
        <div className="module-content">
          <h2>Documents Module</h2>
          <p>Secure document management</p>
          <div className="module-links">
            <Link to="/documents">Documents</Link>
            <Link to="/assets">Assets</Link>
            <Link to="/knowledge">Knowledge Center</Link>
          </div>
        </div>
      )
    },
    {
      id: 'automation',
      title: 'Automation',
      icon: '⚙️',
      content: (
        <div className="module-content">
          <h2>Automation Module</h2>
          <p>Workflow automation and integrations</p>
          <div className="module-links">
            <Link to="/automation">Automation</Link>
            <Link to="/calendar-sync">Calendar Sync</Link>
          </div>
        </div>
      )
    }
  ]

  const currentModule = modules[currentModuleIndex]

  const navigatePrevious = () => {
    setCurrentModuleIndex((prev) => (prev === 0 ? modules.length - 1 : prev - 1))
  }

  const navigateNext = () => {
    setCurrentModuleIndex((prev) => (prev === modules.length - 1 ? 0 : prev + 1))
  }

  const navigateToGrid = () => {
    // Navigate to full grid view or dashboard
    window.location.href = '/'
  }

  const navigateToSettings = () => {
    // Navigate to settings
    window.location.href = '/settings'
  }

  return (
    <div className="command-center">
      {/* Fixed Header */}
      <header className="command-center-header">
        <button 
          className="header-button" 
          onClick={navigateToGrid}
          aria-label="Grid view"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
          </svg>
        </button>
        
        <h1 className="module-title">{currentModule.title}</h1>
        
        <button 
          className="header-button" 
          onClick={navigateToSettings}
          aria-label="Settings"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 1v6m0 6v6m-5.2-9l3 3m4.4 4.4l3 3m-11.6 0l3-3m4.4-4.4l3-3" />
          </svg>
        </button>
      </header>

      {/* Module Content Area */}
      <main className="command-center-content">
        {currentModule.content}
      </main>

      {/* Fixed Bottom Navigation */}
      <nav className="command-center-bottom-nav">
        <button 
          className="nav-button nav-button-left" 
          onClick={navigatePrevious}
          aria-label="Previous module"
        >
          <span className="nav-arrow">&lt;</span>
          <span className="nav-icon">{modules[(currentModuleIndex - 1 + modules.length) % modules.length].icon}</span>
        </button>
        
        <button 
          className="nav-button nav-button-center" 
          aria-label="AI Recommendations"
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
            <circle cx="8" cy="10" r="1.5" />
            <circle cx="16" cy="10" r="1.5" />
            <path d="M12 14c-1.66 0-3 1.34-3 3h6c0-1.66-1.34-3-3-3z" opacity="0.3" />
          </svg>
        </button>
        
        <button 
          className="nav-button nav-button-right" 
          onClick={navigateNext}
          aria-label="Next module"
        >
          <span className="nav-icon">{modules[(currentModuleIndex + 1) % modules.length].icon}</span>
          <span className="nav-arrow">&gt;</span>
        </button>
      </nav>
    </div>
  )
}

export default CommandCenter

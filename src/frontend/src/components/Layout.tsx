import React from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import ImpersonationBanner from './ImpersonationBanner'
import './Layout.css'

const Layout: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="app">
      <ImpersonationBanner />
      <header className="app-header">
        <div className="header-content">
          <div>
            <h1>ConsultantPro</h1>
            <p className="tagline">Quote-to-Cash Management for Consulting Firms</p>
          </div>
          <div className="user-menu">
            <span className="user-name">
              {user?.first_name} {user?.last_name}
            </span>
            <button onClick={handleLogout} className="btn-logout">
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="app-body">
        <nav className="app-nav">
          <Link to="/">📊 Dashboard</Link>

          <div className="nav-section">
            <div className="nav-section-title">CRM & Sales</div>
            <Link to="/crm/leads">🎯 Leads</Link>
            <Link to="/crm/prospects">💼 Prospects</Link>
            <Link to="/crm/campaigns">📢 Campaigns</Link>
            <Link to="/proposals">📄 Proposals</Link>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Client Management</div>
            <Link to="/clients">👥 Clients</Link>
            <Link to="/contracts">📝 Contracts</Link>
            <Link to="/client-portal">🌐 Client Portal</Link>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Delivery</div>
            <Link to="/projects">📋 Projects</Link>
            <Link to="/time-tracking">⏱️ Time Tracking</Link>
            <Link to="/invoices">💰 Invoices</Link>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Resources</div>
            <Link to="/documents">📁 Documents</Link>
            <Link to="/assets">💻 Assets</Link>
            <Link to="/knowledge">📚 Knowledge Center</Link>
            <Link to="/communications">💬 Communications</Link>
          </div>
        </nav>

        <main className="app-main">
          <Outlet />
        </main>
      </div>

      <footer className="app-footer">
        <p>ConsultantPro - Phase 1 | USP Fork-and-Ship Strategy</p>
      </footer>
    </div>
  )
}

export default Layout

import React from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
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

      <nav className="app-nav">
        <Link to="/">Dashboard</Link>
        <Link to="/clients">Clients</Link>
        <Link to="/proposals">Proposals</Link>
        <Link to="/contracts">Contracts</Link>
        <Link to="/projects">Projects</Link>
        <Link to="/time-tracking">Time Tracking</Link>
        <Link to="/invoices">Invoices</Link>
        <Link to="/documents">Documents</Link>
      </nav>

      <main className="app-main">
        <Outlet />
      </main>

      <footer className="app-footer">
        <p>ConsultantPro - Phase 1 | USP Fork-and-Ship Strategy</p>
      </footer>
    </div>
  )
}

export default Layout

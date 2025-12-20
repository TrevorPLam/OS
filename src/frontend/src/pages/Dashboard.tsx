import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { dashboardApi, DashboardStats } from '../api/dashboard'
import './Dashboard.css'

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await dashboardApi.getStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load dashboard stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading dashboard...</div>
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p className="dashboard-subtitle">Your consulting business at a glance</p>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">👥</div>
          <div className="metric-content">
            <h3>{stats?.active_clients || 0}</h3>
            <p>Active Clients</p>
            <span className="metric-detail">of {stats?.total_clients || 0} total</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">📋</div>
          <div className="metric-content">
            <h3>{stats?.accepted_proposals || 0}</h3>
            <p>Accepted Proposals</p>
            <span className="metric-detail">of {stats?.total_proposals || 0} total</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">📄</div>
          <div className="metric-content">
            <h3>{stats?.active_contracts || 0}</h3>
            <p>Active Contracts</p>
            <span className="metric-detail">${parseFloat(stats?.total_contract_value || '0').toLocaleString()} value</span>
          </div>
        </div>

        <div className="metric-card metric-warning">
          <div className="metric-icon">⏰</div>
          <div className="metric-content">
            <h3>{parseFloat(stats?.unbilled_hours || '0').toFixed(1)}h</h3>
            <p>Unbilled Hours</p>
            <span className="metric-detail">Ready to invoice</span>
          </div>
        </div>

        <div className="metric-card metric-alert">
          <div className="metric-icon">💰</div>
          <div className="metric-content">
            <h3>${parseFloat(stats?.total_receivable || '0').toLocaleString()}</h3>
            <p>Accounts Receivable</p>
            <span className="metric-detail">{stats?.unpaid_invoices || 0} unpaid invoices</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          <Link to="/clients" className="action-card">
            <div className="action-icon">+</div>
            <div>
              <h3>Add Client</h3>
              <p>Create a new client record</p>
            </div>
          </Link>
          <Link to="/proposals" className="action-card">
            <div className="action-icon">📝</div>
            <div>
              <h3>New Proposal</h3>
              <p>Draft a proposal</p>
            </div>
          </Link>
          <Link to="/time-tracking" className="action-card">
            <div className="action-icon">⏱️</div>
            <div>
              <h3>Log Time</h3>
              <p>Track your hours</p>
            </div>
          </Link>
          <Link to="/invoices" className="action-card">
            <div className="action-icon">💵</div>
            <div>
              <h3>Create Invoice</h3>
              <p>Bill a client</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Modules Overview */}
      <div className="modules-overview">
        <h2>Platform Modules</h2>
        <div className="module-grid">
          <div className="module-card">
            <h3>CRM</h3>
            <p>Manage clients, proposals, and contracts</p>
            <div className="module-links">
              <Link to="/clients">Clients</Link>
              <Link to="/proposals">Proposals</Link>
              <Link to="/contracts">Contracts</Link>
            </div>
          </div>

          <div className="module-card">
            <h3>Projects</h3>
            <p>Track projects, tasks, and time</p>
            <div className="module-links">
              <Link to="/projects">Projects</Link>
              <Link to="/time-tracking">Time Tracking</Link>
            </div>
          </div>

          <div className="module-card">
            <h3>Finance</h3>
            <p>Handle invoicing and accounting</p>
            <div className="module-links">
              <Link to="/invoices">Invoices</Link>
            </div>
          </div>

          <div className="module-card">
            <h3>Documents</h3>
            <p>Secure document management</p>
            <div className="module-links">
              <Link to="/documents">Documents</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

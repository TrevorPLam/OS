import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Leads from './pages/crm/Leads'
import Prospects from './pages/crm/Prospects'
import Campaigns from './pages/crm/Campaigns'
import Clients from './pages/Clients'
import Proposals from './pages/Proposals'
import Contracts from './pages/Contracts'
import Projects from './pages/Projects'
import ProjectKanban from './pages/ProjectKanban'
import TimeTracking from './pages/TimeTracking'
import Documents from './pages/Documents'
import { ClientPortal } from './pages/ClientPortal'
import { AssetManagement } from './pages/AssetManagement'
import { KnowledgeCenter } from './pages/KnowledgeCenter'
import { Communications } from './pages/Communications'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Dashboard />} />

            {/* CRM Routes */}
            <Route path="/crm/leads" element={<Leads />} />
            <Route path="/crm/prospects" element={<Prospects />} />
            <Route path="/crm/campaigns" element={<Campaigns />} />
            <Route path="/proposals" element={<Proposals />} />

            {/* Client Management Routes */}
            <Route path="/clients" element={<Clients />} />
            <Route path="/contracts" element={<Contracts />} />
            <Route path="/client-portal" element={<ClientPortal />} />

            {/* Delivery Routes */}
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:projectId/kanban" element={<ProjectKanban />} />
            <Route path="/time-tracking" element={<TimeTracking />} />
            <Route path="/invoices" element={<div>Invoices Module (Coming Soon)</div>} />

            {/* Resources Routes */}
            <Route path="/documents" element={<Documents />} />
            <Route path="/assets" element={<AssetManagement />} />
            <Route path="/knowledge" element={<KnowledgeCenter />} />
            <Route path="/communications" element={<Communications />} />
          </Route>

          {/* Catch all - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  </ErrorBoundary>
  )
}

export default App

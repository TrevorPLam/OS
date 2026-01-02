import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ImpersonationProvider } from './contexts/ImpersonationContext'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Leads from './pages/crm/Leads'
import Prospects from './pages/crm/Prospects'
import Campaigns from './pages/crm/Campaigns'
import PipelineKanban from './pages/crm/PipelineKanban'
import PipelineAnalytics from './pages/crm/PipelineAnalytics'
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
import CalendarSync from './pages/CalendarSync'
import CalendarOAuthCallback from './pages/CalendarOAuthCallback'
import Automation from './pages/Automation'
import WorkflowBuilder from './pages/WorkflowBuilder'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <ImpersonationProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/calendar/oauth/callback" element={<CalendarOAuthCallback />} />

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
                <Route path="/crm/pipeline" element={<PipelineKanban />} />
                <Route path="/crm/analytics" element={<PipelineAnalytics />} />
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
                
                {/* Calendar Sync Route */}
                <Route path="/calendar-sync" element={<CalendarSync />} />

                {/* Automation Routes */}
                <Route path="/automation" element={<Automation />} />
                <Route path="/automation/builder/:id" element={<WorkflowBuilder />} />
              </Route>

              {/* Catch all - redirect to home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ImpersonationProvider>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  )
}

export default App

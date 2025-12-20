import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Clients from './pages/Clients'
import Proposals from './pages/Proposals'
import Contracts from './pages/Contracts'
import Projects from './pages/Projects'
import ProjectKanban from './pages/ProjectKanban'
import TimeTracking from './pages/TimeTracking'
import Documents from './pages/Documents'

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
            <Route path="/clients" element={<Clients />} />
            <Route path="/proposals" element={<Proposals />} />
            <Route path="/contracts" element={<Contracts />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:projectId/kanban" element={<ProjectKanban />} />
            <Route path="/time-tracking" element={<TimeTracking />} />
            <Route path="/invoices" element={<div>Invoices Module (Coming Soon)</div>} />
            <Route path="/documents" element={<Documents />} />
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

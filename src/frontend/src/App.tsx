import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>ConsultantPro</h1>
          <p className="tagline">Quote-to-Cash Management for Consulting Firms</p>
        </header>

        <nav className="app-nav">
          <Link to="/">Dashboard</Link>
          <Link to="/clients">Clients</Link>
          <Link to="/proposals">Proposals</Link>
          <Link to="/projects">Projects</Link>
          <Link to="/invoices">Invoices</Link>
        </nav>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clients" element={<div>Clients Module (Coming Soon)</div>} />
            <Route path="/proposals" element={<div>Proposals Module (Coming Soon)</div>} />
            <Route path="/projects" element={<div>Projects Module (Coming Soon)</div>} />
            <Route path="/invoices" element={<div>Invoices Module (Coming Soon)</div>} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>ConsultantPro - Phase 1 Skeleton | USP Fork-and-Ship Strategy</p>
        </footer>
      </div>
    </Router>
  )
}

function Dashboard() {
  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div className="module-grid">
        <ModuleCard
          title="CRM"
          description="Manage clients, proposals, and contracts"
          items={['Leads', 'Proposals', 'Contracts']}
        />
        <ModuleCard
          title="Projects"
          description="Track projects, tasks, and time"
          items={['Projects', 'Tasks', 'Time Entries']}
        />
        <ModuleCard
          title="Finance"
          description="Handle invoicing and accounting"
          items={['Invoices', 'Bills', 'Ledger']}
        />
        <ModuleCard
          title="Documents"
          description="Secure document management"
          items={['Folders', 'Documents', 'Client Portal']}
        />
        <ModuleCard
          title="Assets"
          description="Track company equipment"
          items={['Assets', 'Maintenance']}
        />
      </div>
    </div>
  )
}

interface ModuleCardProps {
  title: string
  description: string
  items: string[]
}

function ModuleCard({ title, description, items }: ModuleCardProps) {
  return (
    <div className="module-card">
      <h3>{title}</h3>
      <p>{description}</p>
      <ul>
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export default App

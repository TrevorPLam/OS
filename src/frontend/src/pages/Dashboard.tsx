import React from 'react'
import './Dashboard.css'

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

const Dashboard: React.FC = () => {
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

export default Dashboard

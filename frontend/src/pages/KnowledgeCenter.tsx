/**
 * Knowledge Center - Internal knowledge management
 * SOPs, org chart, internal wiki, and documentation
 */
import React, { useState } from 'react';
import './KnowledgeCenter.css';

interface SOP {
  id: number;
  title: string;
  category: string;
  description: string;
  lastUpdated: string;
  author: string;
  views: number;
}

interface TeamMember {
  id: number;
  name: string;
  role: string;
  department: string;
  email: string;
  phone: string;
  reportsTo: number | null;
  avatar: string;
}

export const KnowledgeCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'sops' | 'orgchart' | 'wiki'>('sops');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Mock data - replace with API calls
  const [sops] = useState<SOP[]>([
    {
      id: 1,
      title: 'Client Onboarding Process',
      category: 'Sales & Marketing',
      description: 'Step-by-step guide for onboarding new consulting clients',
      lastUpdated: '2025-01-15',
      author: 'Jane Smith',
      views: 245
    },
    {
      id: 2,
      title: 'Project Kickoff Checklist',
      category: 'Project Management',
      description: 'Complete checklist for initiating new client projects',
      lastUpdated: '2025-01-10',
      author: 'John Doe',
      views: 189
    },
    {
      id: 3,
      title: 'Time Entry & Billing Guidelines',
      category: 'Finance',
      description: 'How to properly log time and create client invoices',
      lastUpdated: '2025-01-05',
      author: 'Admin',
      views: 432
    },
    {
      id: 4,
      title: 'Document Management Best Practices',
      category: 'Operations',
      description: 'Guidelines for organizing and sharing client documents',
      lastUpdated: '2024-12-20',
      author: 'Sarah Johnson',
      views: 156
    }
  ]);

  const [teamMembers] = useState<TeamMember[]>([
    {
      id: 1,
      name: 'Robert Chen',
      role: 'Managing Partner',
      department: 'Executive',
      email: 'robert.chen@ubos.com',
      phone: '+1-555-0101',
      reportsTo: null,
      avatar: '👨‍💼'
    },
    {
      id: 2,
      name: 'Sarah Johnson',
      role: 'Senior Consultant',
      department: 'Consulting',
      email: 'sarah.johnson@ubos.com',
      phone: '+1-555-0102',
      reportsTo: 1,
      avatar: '👩‍💼'
    },
    {
      id: 3,
      name: 'Michael Torres',
      role: 'Project Manager',
      department: 'Delivery',
      email: 'michael.torres@ubos.com',
      phone: '+1-555-0103',
      reportsTo: 1,
      avatar: '👨‍💻'
    },
    {
      id: 4,
      name: 'Emily Davis',
      role: 'Business Analyst',
      department: 'Consulting',
      email: 'emily.davis@ubos.com',
      phone: '+1-555-0104',
      reportsTo: 2,
      avatar: '👩‍💻'
    }
  ]);

  const categories = ['all', 'Sales & Marketing', 'Project Management', 'Finance', 'Operations', 'HR'];

  const filteredSOPs = selectedCategory === 'all'
    ? sops
    : sops.filter(sop => sop.category === selectedCategory);

  const getDirectReports = (managerId: number): TeamMember[] => {
    return teamMembers.filter(m => m.reportsTo === managerId);
  };

  return (
    <div className="knowledge-center">
      <header className="knowledge-header">
        <div>
          <h1>Knowledge Center</h1>
          <p>Company procedures, organizational structure, and internal documentation</p>
        </div>
        <button className="btn-primary">+ Create New Document</button>
      </header>

      {/* Tabs */}
      <div className="knowledge-tabs">
        <button
          className={`tab ${activeTab === 'sops' ? 'active' : ''}`}
          onClick={() => setActiveTab('sops')}
        >
          📋 SOPs & Procedures
        </button>
        <button
          className={`tab ${activeTab === 'orgchart' ? 'active' : ''}`}
          onClick={() => setActiveTab('orgchart')}
        >
          🏢 Organization Chart
        </button>
        <button
          className={`tab ${activeTab === 'wiki' ? 'active' : ''}`}
          onClick={() => setActiveTab('wiki')}
        >
          📚 Company Wiki
        </button>
      </div>

      {/* Content */}
      <div className="knowledge-content">
        {activeTab === 'sops' && (
          <div className="sops-section">
            <div className="sops-sidebar">
              <h3>Categories</h3>
              <ul className="category-list">
                {categories.map((category) => (
                  <li
                    key={category}
                    className={selectedCategory === category ? 'active' : ''}
                    onClick={() => setSelectedCategory(category)}
                  >
                    {category === 'all' ? 'All Categories' : category}
                    {category !== 'all' && (
                      <span className="count">
                        ({sops.filter(s => s.category === category).length})
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>

            <div className="sops-main">
              <h2>Standard Operating Procedures</h2>
              <div className="sops-grid">
                {filteredSOPs.map((sop) => (
                  <div key={sop.id} className="sop-card">
                    <div className="sop-header">
                      <span className="sop-category">{sop.category}</span>
                      <span className="sop-views">👁️ {sop.views}</span>
                    </div>
                    <h3>{sop.title}</h3>
                    <p>{sop.description}</p>
                    <div className="sop-footer">
                      <div className="sop-meta">
                        <span>By {sop.author}</span>
                        <span>Updated {new Date(sop.lastUpdated).toLocaleDateString()}</span>
                      </div>
                      <button className="btn-view">View SOP →</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'orgchart' && (
          <div className="orgchart-section">
            <h2>Organization Chart</h2>
            <div className="orgchart">
              {teamMembers
                .filter(member => !member.reportsTo)
                .map((topLevel) => (
                  <div key={topLevel.id} className="org-tree">
                    <div className="org-node">
                      <div className="member-card executive">
                        <div className="member-avatar">{topLevel.avatar}</div>
                        <div className="member-info">
                          <h4>{topLevel.name}</h4>
                          <p className="member-role">{topLevel.role}</p>
                          <p className="member-department">{topLevel.department}</p>
                        </div>
                        <div className="member-contact">
                          <small>{topLevel.email}</small>
                          <small>{topLevel.phone}</small>
                        </div>
                      </div>

                      <div className="org-children">
                        {getDirectReports(topLevel.id).map((child) => (
                          <div key={child.id} className="org-branch">
                            <div className="member-card">
                              <div className="member-avatar">{child.avatar}</div>
                              <div className="member-info">
                                <h4>{child.name}</h4>
                                <p className="member-role">{child.role}</p>
                                <p className="member-department">{child.department}</p>
                              </div>
                              <div className="member-contact">
                                <small>{child.email}</small>
                              </div>
                            </div>

                            {getDirectReports(child.id).length > 0 && (
                              <div className="org-children">
                                {getDirectReports(child.id).map((grandchild) => (
                                  <div key={grandchild.id} className="member-card small">
                                    <div className="member-avatar">{grandchild.avatar}</div>
                                    <div className="member-info">
                                      <h4>{grandchild.name}</h4>
                                      <p className="member-role">{grandchild.role}</p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
            </div>

            <div className="team-directory">
              <h3>Team Directory</h3>
              <table className="directory-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Department</th>
                    <th>Email</th>
                    <th>Phone</th>
                  </tr>
                </thead>
                <tbody>
                  {teamMembers.map((member) => (
                    <tr key={member.id}>
                      <td>
                        <div className="directory-name">
                          <span className="avatar-small">{member.avatar}</span>
                          {member.name}
                        </div>
                      </td>
                      <td>{member.role}</td>
                      <td>{member.department}</td>
                      <td><a href={`mailto:${member.email}`}>{member.email}</a></td>
                      <td>{member.phone}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'wiki' && (
          <div className="wiki-section">
            <h2>Company Wiki</h2>
            <p className="coming-soon">
              Company wiki coming soon. Create and maintain internal documentation,
              best practices, and institutional knowledge.
            </p>
            <div className="wiki-placeholder">
              <div className="wiki-card">
                <h3>📖 Getting Started</h3>
                <p>New hire onboarding and company overview</p>
              </div>
              <div className="wiki-card">
                <h3>🛠️ Tools & Systems</h3>
                <p>Guide to all software and platforms we use</p>
              </div>
              <div className="wiki-card">
                <h3>📞 Client Communication</h3>
                <p>Templates and best practices for client interactions</p>
              </div>
              <div className="wiki-card">
                <h3>💡 Best Practices</h3>
                <p>Lessons learned and recommended approaches</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

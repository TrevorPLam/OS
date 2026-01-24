import React, { useEffect, useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MarkerType,
  Node,
  Panel,
  useEdgesState,
  useNodesState,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { ContactGraphNode, useContactGraphView } from '../../api/crm'
import './ContactGraphView.css'

type ContactNodeData = ContactGraphNode['data'] & { strength: number }

const ContactNode = ({ data }: { data: ContactNodeData }) => {
  return (
    <div className={`contact-node ${data.is_primary ? 'primary' : ''} ${data.is_decision_maker ? 'decision-maker' : ''}`}>
      <div className="contact-node-header">
        <strong>{data.name}</strong>
        {data.is_primary && <span className="badge">Primary</span>}
        {data.is_decision_maker && <span className="badge dm">DM</span>}
      </div>
      <div className="contact-node-body">
        {data.job_title && <div className="job-title">{data.job_title}</div>}
        {data.email && <div className="email">{data.email}</div>}
        <div className="account">{data.account_name}</div>
      </div>
      <div className="strength-indicator" style={{ width: `${data.strength * 100}%` }} />
    </div>
  )
}

const AccountNode = ({ data }: { data: ContactNodeData }) => {
  return (
    <div className={`account-node ${data.account_type || ''}`}>
      <div className="account-node-header">
        <strong>{data.name}</strong>
        <span className="type-badge">{data.account_type || 'N/A'}</span>
      </div>
      {data.industry && (
        <div className="account-node-body">
          <div className="industry">{data.industry}</div>
        </div>
      )}
    </div>
  )
}

const nodeTypes = {
  contact: ContactNode,
  account: AccountNode,
}

const ContactGraphView: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const [filterContactId, setFilterContactId] = useState<string>('')
  const [filterDepth, setFilterDepth] = useState<number>(2)
  const [includeInactive, setIncludeInactive] = useState(false)
  const [showContactsOnly, setShowContactsOnly] = useState(false)
  const [showAccountsOnly, setShowAccountsOnly] = useState(false)

  const contactId = useMemo(() => {
    if (!filterContactId.trim()) return undefined
    const parsed = parseInt(filterContactId, 10)
    return Number.isNaN(parsed) ? undefined : parsed
  }, [filterContactId])

  const {
    data: graphData,
    isLoading,
    isError,
    error,
    refetch,
  } = useContactGraphView({
    contact_id: contactId,
    depth: filterDepth,
    include_inactive: includeInactive,
  })

  useEffect(() => {
    if (!graphData) return

    const flowNodes: Node<ContactNodeData>[] = graphData.nodes
      .filter((node) => {
        if (showContactsOnly) return node.type === 'contact'
        if (showAccountsOnly) return node.type === 'account'
        return true
      })
      .map((node, index) => ({
        id: node.id,
        type: node.type,
        data: {
          ...node.data,
          strength: node.strength,
        },
        position: calculateNodePosition(index, graphData.nodes.length, node.type),
        style: {
          opacity: 0.7 + node.strength * 0.3,
        },
      }))

    const flowEdges: Edge[] = graphData.edges
      .filter((edge) => {
        const sourceVisible = flowNodes.some((node) => node.id === edge.source)
        const targetVisible = flowNodes.some((node) => node.id === edge.target)
        return sourceVisible && targetVisible
      })
      .map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        animated: edge.type === 'relationship',
        style: {
          stroke: edge.type === 'relationship' ? '#10b981' : '#94a3b8',
          strokeWidth: 1 + edge.strength * 2,
          opacity: 0.5 + edge.strength * 0.5,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edge.type === 'relationship' ? '#10b981' : '#94a3b8',
        },
        label: edge.relationship_type ? edge.relationship_type.replace('_', ' ') : undefined,
      }))

    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [graphData, setEdges, setNodes, showAccountsOnly, showContactsOnly])

  const calculateNodePosition = (index: number, total: number, type: string) => {
    const radius = type === 'contact' ? 300 : 500
    const angle = (index / total) * 2 * Math.PI

    return {
      x: 400 + radius * Math.cos(angle),
      y: 300 + radius * Math.sin(angle),
    }
  }

  const handleExportImage = () => {
    alert('Export functionality: In production, this would export the graph as PNG/SVG')
  }

  const handleResetFilters = () => {
    setFilterContactId('')
    setFilterDepth(2)
    setIncludeInactive(false)
    setShowContactsOnly(false)
    setShowAccountsOnly(false)
  }

  if (isLoading) {
    return (
      <div className="contact-graph-container">
        <div className="loading">Loading contact graph...</div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="contact-graph-container">
        <div className="error">
          <h3>Error Loading Graph</h3>
          <p>{error instanceof Error ? error.message : 'Failed to load graph data'}</p>
          <button onClick={() => refetch()}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="contact-graph-container">
      <div className="graph-header">
        <h1>Contact 360° Graph View</h1>
        <div className="graph-stats">
          <div className="stat">
            <span className="stat-value">{graphData?.metadata.total_contacts || 0}</span>
            <span className="stat-label">Contacts</span>
          </div>
          <div className="stat">
            <span className="stat-value">{graphData?.metadata.total_accounts || 0}</span>
            <span className="stat-label">Accounts</span>
          </div>
          <div className="stat">
            <span className="stat-value">{graphData?.metadata.total_relationships || 0}</span>
            <span className="stat-label">Relationships</span>
          </div>
        </div>
      </div>

      <div className="graph-controls">
        <div className="control-group">
          <label>
            Focus Contact ID:
            <input
              type="text"
              value={filterContactId}
              onChange={(e) => setFilterContactId(e.target.value)}
              placeholder="Enter contact ID"
            />
          </label>

          <label>
            Depth:
            <select value={filterDepth} onChange={(e) => setFilterDepth(parseInt(e.target.value, 10))}>
              <option value="1">1 level</option>
              <option value="2">2 levels</option>
              <option value="3">3 levels</option>
            </select>
          </label>

          <label className="checkbox">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            Include Inactive
          </label>

          <label className="checkbox">
            <input
              type="checkbox"
              checked={showContactsOnly}
              onChange={(e) => {
                setShowContactsOnly(e.target.checked)
                if (e.target.checked) setShowAccountsOnly(false)
              }}
            />
            Contacts Only
          </label>

          <label className="checkbox">
            <input
              type="checkbox"
              checked={showAccountsOnly}
              onChange={(e) => {
                setShowAccountsOnly(e.target.checked)
                if (e.target.checked) setShowContactsOnly(false)
              }}
            />
            Accounts Only
          </label>
        </div>

        <div className="action-buttons">
          <button onClick={() => refetch()} className="btn-primary">
            Refresh
          </button>
          <button onClick={handleResetFilters} className="btn-secondary">
            Reset Filters
          </button>
          <button onClick={handleExportImage} className="btn-secondary">
            Export as Image
          </button>
        </div>
      </div>

      <div className="graph-view">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.1}
          maxZoom={2}
        >
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          <Controls />
          <Panel position="bottom-right">
            <div className="legend">
              <div className="legend-item">
                <div className="legend-color contact" />
                <span>Contact</span>
              </div>
              <div className="legend-item">
                <div className="legend-color account" />
                <span>Account</span>
              </div>
              <div className="legend-item">
                <div className="legend-line relationship" />
                <span>Account Relationship</span>
              </div>
              <div className="legend-item">
                <div className="legend-line belongs-to" />
                <span>Belongs To</span>
              </div>
            </div>
          </Panel>
        </ReactFlow>
      </div>

      <div className="graph-info">
        <h3>Instructions</h3>
        <ul>
          <li>Zoom: Mouse wheel or pinch gesture</li>
          <li>Pan: Click and drag the canvas</li>
          <li>Move nodes: Click and drag individual nodes</li>
          <li>Relationship strength: Indicated by edge thickness and node opacity</li>
          <li>Focus on a contact: Enter contact ID in the filter above</li>
        </ul>
      </div>
    </div>
  )
}

export default ContactGraphView

/**
 * Workflow Builder Component (AUTO-4).
 *
 * Visual workflow builder with drag-and-drop canvas:
 * - Node management (add, edit, delete)
 * - Edge management (connections)
 * - Trigger configuration
 * - Goal setup
 * - Testing mode
 *
 * This is a simplified implementation. For production, consider using
 * React Flow (https://reactflow.dev/) or similar library.
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getWorkflow,
  getTriggers,
  createTrigger,
  deleteTrigger,
  getNodes,
  createNode,
  deleteNode,
} from '../api/automation';
import './WorkflowBuilder.css';

interface WorkflowNodeView {
  id: number;
  node_type: string;
  node_type_display?: string;
  label?: string;
}

interface WorkflowTriggerView {
  id: number;
  trigger_type_display?: string;
  is_active?: boolean;
}

const WorkflowBuilder: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'canvas' | 'triggers' | 'settings'>('canvas');
  const [showTriggerModal, setShowTriggerModal] = useState(false);

  // Fetch workflow
  const { data: workflow, isLoading: workflowLoading } = useQuery({
    queryKey: ['workflow', id],
    queryFn: () => getWorkflow(Number(id)),
    enabled: !!id,
  });

  // Fetch triggers
  const { data: triggers = [] } = useQuery<WorkflowTriggerView[]>({
    queryKey: ['triggers', id],
    queryFn: () => getTriggers(Number(id)),
    enabled: !!id,
  });

  // Fetch nodes
  const { data: nodes = [] } = useQuery<WorkflowNodeView[]>({
    queryKey: ['nodes', id],
    queryFn: () => getNodes(Number(id)),
    enabled: !!id,
  });

  // Create node mutation
  const createNodeMutation = useMutation({
    mutationFn: createNode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes', id] });
    },
  });

  // Delete node mutation
  const deleteNodeMutation = useMutation({
    mutationFn: deleteNode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes', id] });
    },
  });

  // Create trigger mutation
  const createTriggerMutation = useMutation({
    mutationFn: createTrigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers', id] });
      setShowTriggerModal(false);
    },
  });

  // Delete trigger mutation
  const deleteTriggerMutation = useMutation({
    mutationFn: deleteTrigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers', id] });
    },
  });

  const handleAddNode = (nodeType: string) => {
    const newNode = {
      workflow: Number(id),
      node_id: `node_${Date.now()}`,
      node_type: nodeType,
      label: getNodeLabel(nodeType),
      position_x: Math.floor(Math.random() * 400) + 100,
      position_y: Math.floor(Math.random() * 300) + 100,
      configuration: {},
    };

    createNodeMutation.mutate(newNode);
  };

  const handleDeleteNode = (nodeId: number) => {
    if (window.confirm('Are you sure you want to delete this node?')) {
      deleteNodeMutation.mutate(nodeId);
    }
  };

  const getNodeLabel = (nodeType: string): string => {
    const labels: Record<string, string> = {
      send_email: 'Send Email',
      send_sms: 'Send SMS',
      create_task: 'Create Task',
      create_deal: 'Create Deal',
      update_deal: 'Update Deal',
      update_contact: 'Update Contact',
      add_tag: 'Add Tag',
      remove_tag: 'Remove Tag',
      condition: 'If/Else',
      wait_time: 'Wait',
      goal: 'Goal',
    };
    return labels[nodeType] || nodeType;
  };

  const nodeCategories = [
    {
      name: 'Actions',
      nodes: [
        { type: 'send_email', icon: '📧', label: 'Send Email' },
        { type: 'send_sms', icon: '💬', label: 'Send SMS' },
        { type: 'create_task', icon: '✓', label: 'Create Task' },
        { type: 'create_deal', icon: '💼', label: 'Create Deal' },
        { type: 'update_contact', icon: '👤', label: 'Update Contact' },
        { type: 'add_tag', icon: '🏷️', label: 'Add Tag' },
      ],
    },
    {
      name: 'Control Flow',
      nodes: [
        { type: 'condition', icon: '❓', label: 'If/Else' },
        { type: 'wait_time', icon: '⏰', label: 'Wait' },
        { type: 'split', icon: '🔀', label: 'A/B Split' },
      ],
    },
    {
      name: 'Goals',
      nodes: [
        { type: 'goal', icon: '🎯', label: 'Goal' },
      ],
    },
  ];

  if (workflowLoading) {
    return <div className="builder-loading">Loading workflow...</div>;
  }

  if (!workflow) {
    return <div className="builder-error">Workflow not found</div>;
  }

  return (
    <div className="workflow-builder">
      <div className="builder-header">
        <button className="btn-back" onClick={() => navigate('/automation')}>
          ← Back
        </button>
        <h1>{workflow.name}</h1>
        <div className="header-actions">
          <span className={`status-badge status-${workflow.status}`}>
            {workflow.status_display}
          </span>
        </div>
      </div>

      <div className="builder-tabs">
        <button
          className={activeTab === 'canvas' ? 'tab-active' : ''}
          onClick={() => setActiveTab('canvas')}
        >
          Canvas
        </button>
        <button
          className={activeTab === 'triggers' ? 'tab-active' : ''}
          onClick={() => setActiveTab('triggers')}
        >
          Triggers ({triggers.length})
        </button>
        <button
          className={activeTab === 'settings' ? 'tab-active' : ''}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
      </div>

      {activeTab === 'canvas' && (
        <div className="builder-canvas-container">
          <div className="canvas-sidebar">
            <h3>Add Nodes</h3>
            {nodeCategories.map((category) => (
              <div key={category.name} className="node-category">
                <h4>{category.name}</h4>
                <div className="node-palette">
                  {category.nodes.map((node) => (
                    <button
                      key={node.type}
                      className="node-palette-item"
                      onClick={() => handleAddNode(node.type)}
                    >
                      <span className="node-icon">{node.icon}</span>
                      <span className="node-label">{node.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="canvas-main">
            <div className="canvas-area">
              {nodes.length === 0 ? (
                <div className="canvas-empty">
                  <p>No nodes yet. Add nodes from the sidebar to get started.</p>
                </div>
              ) : (
                <div className="nodes-list">
                  {nodes.map((node) => (
                    <div key={node.id} className="node-item">
                      <div className="node-header">
                        <strong>{node.label}</strong>
                        <span className="node-type">{node.node_type_display}</span>
                      </div>
                      <div className="node-actions">
                        <button
                          className="btn-edit-node"
                          disabled
                          title="Node editing is planned but not implemented yet."
                        >
                          Edit
                        </button>
                        <button
                          className="btn-delete-node"
                          onClick={() => handleDeleteNode(node.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'triggers' && (
        <div className="builder-triggers">
          <div className="triggers-header">
            <h3>Workflow Triggers</h3>
            <button
              className="btn-add-trigger"
              onClick={() => setShowTriggerModal(true)}
            >
              + Add Trigger
            </button>
          </div>

          {triggers.length === 0 ? (
            <div className="no-triggers">
              <p>No triggers configured. Add a trigger to activate this workflow.</p>
            </div>
          ) : (
            <div className="triggers-list">
              {triggers.map((trigger) => (
                <div key={trigger.id} className="trigger-item">
                  <div className="trigger-header">
                    <strong>{trigger.trigger_type_display}</strong>
                    <span className={`trigger-status ${trigger.is_active ? 'active' : 'inactive'}`}>
                      {trigger.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="trigger-actions">
                    <button
                      className="btn-delete-trigger"
                      onClick={() => deleteTriggerMutation.mutate(trigger.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="builder-settings">
          <h3>Workflow Settings</h3>
          <div className="settings-form">
            <div className="form-group">
              <label>Workflow Name</label>
              <input
                type="text"
                value={workflow.name}
                readOnly
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={workflow.description || ''}
                readOnly
                rows={3}
              />
            </div>
            <div className="form-group">
              <label>Status</label>
              <input
                type="text"
                value={workflow.status_display}
                readOnly
              />
            </div>
          </div>
        </div>
      )}

      {/* Add Trigger Modal */}
      {showTriggerModal && (
        <div className="modal-overlay" onClick={() => setShowTriggerModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add Trigger</h2>
            <p>Select a trigger type to add to this workflow:</p>
            <div className="trigger-types">
              {[
                { type: 'form_submitted', label: 'Form Submitted' },
                { type: 'contact_created', label: 'Contact Created' },
                { type: 'deal_created', label: 'Deal Created' },
                { type: 'email_opened', label: 'Email Opened' },
                { type: 'manual', label: 'Manual Trigger' },
              ].map((triggerType) => (
                <button
                  key={triggerType.type}
                  className="trigger-type-btn"
                  onClick={() => {
                    createTriggerMutation.mutate({
                      workflow: Number(id),
                      trigger_type: triggerType.type,
                      configuration: {},
                      filter_conditions: {},
                      is_active: true,
                    });
                  }}
                >
                  {triggerType.label}
                </button>
              ))}
            </div>
            <div className="modal-actions">
              <button
                className="btn-cancel"
                onClick={() => setShowTriggerModal(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowBuilder;

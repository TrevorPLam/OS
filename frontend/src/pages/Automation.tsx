/**
 * Automation Workflow Management Page (AUTO-4).
 *
 * Main page for managing automation workflows:
 * - List of workflows
 * - Create/edit/delete workflows
 * - Activate/pause workflows
 * - View analytics
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getWorkflows,
  createWorkflow,
  deleteWorkflow,
  activateWorkflow,
  pauseWorkflow,
  duplicateWorkflow,
} from '../api/automation';
import './Automation.css';

interface Workflow {
  id: number;
  name: string;
  description: string;
  status: string;
  status_display: string;
  version: number;
  trigger_count?: number;
  node_count?: number;
  execution_count?: number;
  activated_at?: string;
  created_at: string;
  updated_at: string;
}

const Automation: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('');
  const [newWorkflowDescription, setNewWorkflowDescription] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  // Fetch workflows
  const { data: workflows = [], isLoading, error } = useQuery({
    queryKey: ['workflows'],
    queryFn: getWorkflows,
  });

  // Create workflow mutation
  const createMutation = useMutation({
    mutationFn: createWorkflow,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      setShowCreateModal(false);
      setNewWorkflowName('');
      setNewWorkflowDescription('');
      navigate(`/automation/builder/${data.id}`);
    },
  });

  // Delete workflow mutation
  const deleteMutation = useMutation({
    mutationFn: deleteWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  // Activate workflow mutation
  const activateMutation = useMutation({
    mutationFn: activateWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  // Pause workflow mutation
  const pauseMutation = useMutation({
    mutationFn: pauseWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  // Duplicate workflow mutation
  const duplicateMutation = useMutation({
    mutationFn: duplicateWorkflow,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      navigate(`/automation/builder/${data.id}`);
    },
  });

  const handleCreateWorkflow = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      name: newWorkflowName,
      description: newWorkflowDescription,
      status: 'draft',
    });
  };

  const handleDeleteWorkflow = (id: number) => {
    if (window.confirm('Are you sure you want to delete this workflow?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleActivateWorkflow = (id: number) => {
    activateMutation.mutate(id);
  };

  const handlePauseWorkflow = (id: number) => {
    pauseMutation.mutate(id);
  };

  const handleDuplicateWorkflow = (id: number) => {
    duplicateMutation.mutate(id);
  };

  // Filter workflows
  const filteredWorkflows = workflows.filter((workflow: Workflow) => {
    if (filterStatus === 'all') return true;
    return workflow.status === filterStatus;
  });

  if (isLoading) {
    return <div className="automation-loading">Loading workflows...</div>;
  }

  if (error) {
    return <div className="automation-error">Error loading workflows: {String(error)}</div>;
  }

  return (
    <div className="automation-container">
      <div className="automation-header">
        <h1>Automation Workflows</h1>
        <button
          className="btn-create-workflow"
          onClick={() => setShowCreateModal(true)}
        >
          + Create Workflow
        </button>
      </div>

      <div className="automation-filters">
        <div className="filter-group">
          <label>Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">All</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      <div className="workflows-list">
        {filteredWorkflows.length === 0 ? (
          <div className="no-workflows">
            <p>No workflows found.</p>
            <button onClick={() => setShowCreateModal(true)}>
              Create your first workflow
            </button>
          </div>
        ) : (
          <div className="workflows-grid">
            {filteredWorkflows.map((workflow: Workflow) => (
              <div key={workflow.id} className="workflow-card">
                <div className="workflow-card-header">
                  <h3>{workflow.name}</h3>
                  <span className={`status-badge status-${workflow.status}`}>
                    {workflow.status_display}
                  </span>
                </div>

                <p className="workflow-description">
                  {workflow.description || 'No description'}
                </p>

                <div className="workflow-stats">
                  <div className="stat">
                    <span className="stat-value">{workflow.trigger_count || 0}</span>
                    <span className="stat-label">Triggers</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{workflow.node_count || 0}</span>
                    <span className="stat-label">Nodes</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{workflow.execution_count || 0}</span>
                    <span className="stat-label">Executions</span>
                  </div>
                </div>

                <div className="workflow-actions">
                  <button
                    className="btn-edit"
                    onClick={() => navigate(`/automation/builder/${workflow.id}`)}
                  >
                    Edit
                  </button>

                  {workflow.status === 'draft' || workflow.status === 'paused' ? (
                    <button
                      className="btn-activate"
                      onClick={() => handleActivateWorkflow(workflow.id)}
                    >
                      Activate
                    </button>
                  ) : null}

                  {workflow.status === 'active' ? (
                    <button
                      className="btn-pause"
                      onClick={() => handlePauseWorkflow(workflow.id)}
                    >
                      Pause
                    </button>
                  ) : null}

                  <button
                    className="btn-duplicate"
                    onClick={() => handleDuplicateWorkflow(workflow.id)}
                  >
                    Duplicate
                  </button>

                  <button
                    className="btn-analytics"
                    onClick={() => navigate(`/automation/analytics/${workflow.id}`)}
                  >
                    Analytics
                  </button>

                  <button
                    className="btn-delete"
                    onClick={() => handleDeleteWorkflow(workflow.id)}
                  >
                    Delete
                  </button>
                </div>

                <div className="workflow-meta">
                  <small>
                    Version {workflow.version} · Created{' '}
                    {new Date(workflow.created_at).toLocaleDateString()}
                  </small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Workflow Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Workflow</h2>
            <form onSubmit={handleCreateWorkflow}>
              <div className="form-group">
                <label>Workflow Name *</label>
                <input
                  type="text"
                  value={newWorkflowName}
                  onChange={(e) => setNewWorkflowName(e.target.value)}
                  placeholder="Enter workflow name"
                  required
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newWorkflowDescription}
                  onChange={(e) => setNewWorkflowDescription(e.target.value)}
                  placeholder="Enter workflow description"
                  rows={3}
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-submit"
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Workflow'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Automation;

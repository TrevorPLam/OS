/**
 * API client for Automation Workflow System.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Workflow API
export const getWorkflows = async () => {
  const response = await axios.get(`${API_BASE_URL}/automation/workflows/`);
  return response.data;
};

export const getWorkflow = async (id: number) => {
  const response = await axios.get(`${API_BASE_URL}/automation/workflows/${id}/`);
  return response.data;
};

export const createWorkflow = async (data: any) => {
  const response = await axios.post(`${API_BASE_URL}/automation/workflows/`, data);
  return response.data;
};

export const updateWorkflow = async (id: number, data: any) => {
  const response = await axios.patch(`${API_BASE_URL}/automation/workflows/${id}/`, data);
  return response.data;
};

export const deleteWorkflow = async (id: number) => {
  await axios.delete(`${API_BASE_URL}/automation/workflows/${id}/`);
};

export const activateWorkflow = async (id: number) => {
  const response = await axios.post(`${API_BASE_URL}/automation/workflows/${id}/activate/`);
  return response.data;
};

export const pauseWorkflow = async (id: number) => {
  const response = await axios.post(`${API_BASE_URL}/automation/workflows/${id}/pause/`);
  return response.data;
};

export const duplicateWorkflow = async (id: number) => {
  const response = await axios.post(`${API_BASE_URL}/automation/workflows/${id}/duplicate/`);
  return response.data;
};

export const getWorkflowAnalytics = async (id: number) => {
  const response = await axios.get(`${API_BASE_URL}/automation/workflows/${id}/analytics/`);
  return response.data;
};

export const getWorkflowExecutions = async (id: number) => {
  const response = await axios.get(`${API_BASE_URL}/automation/workflows/${id}/executions/`);
  return response.data;
};

// Trigger API
export const getTriggers = async (workflowId?: number) => {
  const params = workflowId ? { workflow: workflowId } : {};
  const response = await axios.get(`${API_BASE_URL}/automation/triggers/`, { params });
  return response.data;
};

export const createTrigger = async (data: any) => {
  const response = await axios.post(`${API_BASE_URL}/automation/triggers/`, data);
  return response.data;
};

export const updateTrigger = async (id: number, data: any) => {
  const response = await axios.patch(`${API_BASE_URL}/automation/triggers/${id}/`, data);
  return response.data;
};

export const deleteTrigger = async (id: number) => {
  await axios.delete(`${API_BASE_URL}/automation/triggers/${id}/`);
};

// Node API
export const getNodes = async (workflowId?: number) => {
  const params = workflowId ? { workflow: workflowId } : {};
  const response = await axios.get(`${API_BASE_URL}/automation/nodes/`, { params });
  return response.data;
};

export const createNode = async (data: any) => {
  const response = await axios.post(`${API_BASE_URL}/automation/nodes/`, data);
  return response.data;
};

export const updateNode = async (id: number, data: any) => {
  const response = await axios.patch(`${API_BASE_URL}/automation/nodes/${id}/`, data);
  return response.data;
};

export const deleteNode = async (id: number) => {
  await axios.delete(`${API_BASE_URL}/automation/nodes/${id}/`);
};

// Edge API
export const getEdges = async (workflowId?: number) => {
  const params = workflowId ? { workflow: workflowId } : {};
  const response = await axios.get(`${API_BASE_URL}/automation/edges/`, { params });
  return response.data;
};

export const createEdge = async (data: any) => {
  const response = await axios.post(`${API_BASE_URL}/automation/edges/`, data);
  return response.data;
};

export const deleteEdge = async (id: number) => {
  await axios.delete(`${API_BASE_URL}/automation/edges/${id}/`);
};

// Execution API
export const getExecutions = async (params?: any) => {
  const response = await axios.get(`${API_BASE_URL}/automation/executions/`, { params });
  return response.data;
};

export const getExecution = async (id: number) => {
  const response = await axios.get(`${API_BASE_URL}/automation/executions/${id}/`);
  return response.data;
};

export const cancelExecution = async (id: number) => {
  const response = await axios.post(`${API_BASE_URL}/automation/executions/${id}/cancel/`);
  return response.data;
};

export const retryExecution = async (id: number) => {
  const response = await axios.post(`${API_BASE_URL}/automation/executions/${id}/retry/`);
  return response.data;
};

export const getExecutionFlowVisualization = async (id: number) => {
  const response = await axios.get(`${API_BASE_URL}/automation/executions/${id}/flow_visualization/`);
  return response.data;
};

// Goal API
export const getGoals = async (workflowId?: number) => {
  const params = workflowId ? { workflow: workflowId } : {};
  const response = await axios.get(`${API_BASE_URL}/automation/goals/`, { params });
  return response.data;
};

export const createGoal = async (data: any) => {
  const response = await axios.post(`${API_BASE_URL}/automation/goals/`, data);
  return response.data;
};

export const updateGoal = async (id: number, data: any) => {
  const response = await axios.patch(`${API_BASE_URL}/automation/goals/${id}/`, data);
  return response.data;
};

export const deleteGoal = async (id: number) => {
  await axios.delete(`${API_BASE_URL}/automation/goals/${id}/`);
};

export const updateGoalAnalytics = async (id: number) => {
  const response = await axios.post(`${API_BASE_URL}/automation/goals/${id}/update_analytics/`);
  return response.data;
};

// Analytics API
export const getAllAnalytics = async (params?: any) => {
  const response = await axios.get(`${API_BASE_URL}/automation/analytics/`, { params });
  return response.data;
};

export const getAnalytics = async (id: number) => {
  const response = await axios.get(`${API_BASE_URL}/automation/analytics/${id}/`);
  return response.data;
};

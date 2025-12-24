/**
 * API client for Assets module
 */
import apiClient from './client';

export interface Asset {
  id: number;
  asset_tag: string;
  name: string;
  description: string;
  category: string;
  status: string;
  assigned_to: number | null;
  assigned_to_name: string;
  purchase_price: string;
  purchase_date: string;
  useful_life_years: number;
  salvage_value: string;
  manufacturer: string;
  model_number: string;
  serial_number: string;
  location: string;
  warranty_expiration: string | null;
  created_at: string;
  updated_at: string;
  notes: string;
}

export interface MaintenanceLog {
  id: number;
  asset: number;
  asset_tag: string;
  asset_name: string;
  maintenance_type: string;
  status: string;
  description: string;
  scheduled_date: string;
  completed_date: string | null;
  performed_by: string;
  vendor: string;
  cost: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface AssetsListParams {
  category?: string;
  status?: string;
  assigned_to?: number;
  search?: string;
  ordering?: string;
  page?: number;
}

export const assetsApi = {
  // Assets
  listAssets: (params?: AssetsListParams) =>
    apiClient.get('/assets/assets/', { params }),

  getAsset: (id: number) =>
    apiClient.get(`/assets/assets/${id}/`),

  createAsset: (data: Partial<Asset>) =>
    apiClient.post('/assets/assets/', data),

  updateAsset: (id: number, data: Partial<Asset>) =>
    apiClient.patch(`/assets/assets/${id}/`, data),

  deleteAsset: (id: number) =>
    apiClient.delete(`/assets/assets/${id}/`),

  // Maintenance Logs
  listMaintenanceLogs: (params?: { asset?: number; status?: string }) =>
    apiClient.get('/assets/maintenance-logs/', { params }),

  getMaintenanceLog: (id: number) =>
    apiClient.get(`/assets/maintenance-logs/${id}/`),

  createMaintenanceLog: (data: Partial<MaintenanceLog>) =>
    apiClient.post('/assets/maintenance-logs/', data),

  updateMaintenanceLog: (id: number, data: Partial<MaintenanceLog>) =>
    apiClient.patch(`/assets/maintenance-logs/${id}/`, data),

  deleteMaintenanceLog: (id: number) =>
    apiClient.delete(`/assets/maintenance-logs/${id}/`),
};

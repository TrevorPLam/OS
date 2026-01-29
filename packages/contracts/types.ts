/**
 * Shared TypeScript types for OS API contracts
 * 
 * These types should match the Django backend API structure.
 */

// API Response types
export interface ApiResponse<T> {
  data: T;
  error?: string;
}

// Common domain types
export type ClientId = string;
export type ProjectId = string;
export type DocumentId = string;
export type AssetId = string;

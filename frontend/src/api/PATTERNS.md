# Code Patterns - API Clients

**Folder:** `frontend/src/api/`

This document contains common code patterns for API client functions. Use these patterns to maintain consistency.

## Query Hook Pattern

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';

export const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: () => apiClient.get('/api/clients/')
  });
};
```

## Mutation Hook Pattern

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';

export const useCreateClient = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ClientData) => apiClient.post('/api/clients/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    }
  });
};
```

## Query with Parameters Pattern

```typescript
export const useClient = (id: string) => {
  return useQuery({
    queryKey: ['clients', id],
    queryFn: () => apiClient.get(`/api/clients/${id}/`),
    enabled: !!id
  });
};
```

## Error Handling Pattern

```typescript
export const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: () => apiClient.get('/api/clients/'),
    onError: (error) => {
      console.error('Failed to fetch clients:', error);
      // Handle error (show toast, etc.)
    }
  });
};
```

## Anti-Patterns (Don't Do This)

```typescript
// ❌ Bad: Direct fetch call
export const getClients = async () => {
  const response = await fetch('/api/clients/');
  return response.json();
};

// ✅ Good: Use React Query
export const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: () => apiClient.get('/api/clients/')
  });
};

// ❌ Bad: Missing TypeScript types
export const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: () => apiClient.get('/api/clients/')
  });
};

// ✅ Good: With TypeScript types
export const useClients = (): UseQueryResult<Client[]> => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: () => apiClient.get<Client[]>('/api/clients/')
  });
};
```

---

**Note:** These patterns are examples. Always check existing code in this folder for the most current patterns.

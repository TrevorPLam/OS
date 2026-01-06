# AGENTS.md — Frontend (React + TypeScript)

Last Updated: 2026-01-06
Applies To: `src/frontend/`

## Purpose

React + TypeScript frontend application built with Vite.

## Tech Stack

- **React 18** with TypeScript
- **Vite** build tool
- **React Router** for routing
- **React Query** (TanStack Query) for data fetching
- **Axios** for HTTP client
- **React Flow** for visual workflow builder

## Directory Structure

```
frontend/
├── src/
│   ├── api/              # API client modules
│   ├── components/       # Reusable components
│   ├── contexts/         # React contexts
│   ├── pages/            # Page components
│   │   └── crm/          # CRM-specific pages
│   └── tracking/         # Analytics tracking
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

## Running the Frontend

```bash
cd src/frontend
npm install
npm run dev           # Development server (port 5173)
npm run build         # Production build
```

## Environment Variables

```bash
# .env or .env.local
VITE_API_URL=http://localhost:8000/api
```

## Key Patterns

### API Client

See `src/api/client.ts`:

```typescript
import apiClient from './api/client'

// All requests include auth token automatically
const response = await apiClient.get('/clients/')
```

### Authentication Context

See `src/contexts/AuthContext.tsx`:

```typescript
import { useAuth } from './contexts/AuthContext'

const { user, login, logout, isAuthenticated } = useAuth()
```

### Protected Routes

See `src/components/ProtectedRoute.tsx`:

```typescript
<Route element={<ProtectedRoute />}>
  <Route path="/dashboard" element={<Dashboard />} />
</Route>
```

### Impersonation Banner

See `src/contexts/ImpersonationContext.tsx`:
- Detects `X-Break-Glass-Impersonation` header
- Shows warning banner when active

## Page Organization

| Path | Component | Purpose |
|------|-----------|---------|
| `/login` | Login | Authentication |
| `/dashboard` | Dashboard | Main dashboard |
| `/clients` | Clients | Client list |
| `/crm/leads` | Leads | Lead management |
| `/crm/prospects` | Prospects | Prospect management |
| `/crm/deals` | Deals | Deal pipeline |
| `/projects` | Projects | Project list |
| `/documents` | Documents | Document management |
| `/calendar` | CalendarSync | Calendar settings |
| `/automation` | Automation | Workflow list |
| `/workflow-builder` | WorkflowBuilder | Visual workflow editor |

## Component Patterns

### Page Component

```typescript
// src/pages/MyPage.tsx
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

export function MyPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['my-data'],
    queryFn: () => apiClient.get('/my-endpoint/'),
  })

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorBoundary error={error} />

  return <div>{/* render data */}</div>
}
```

### API Module

```typescript
// src/api/myModule.ts
import apiClient from './client'

export const myApi = {
  list: () => apiClient.get('/my-endpoint/'),
  get: (id: string) => apiClient.get(`/my-endpoint/${id}/`),
  create: (data: MyType) => apiClient.post('/my-endpoint/', data),
  update: (id: string, data: MyType) => apiClient.put(`/my-endpoint/${id}/`, data),
  delete: (id: string) => apiClient.delete(`/my-endpoint/${id}/`),
}
```

## Styling

- CSS files alongside components (e.g., `Dashboard.css`)
- No CSS-in-JS currently
- Consider migrating to Tailwind (TODO)

## Dependencies

- **Depends on**: Backend API (`src/api/`)
- **Key libs**: See `package.json`

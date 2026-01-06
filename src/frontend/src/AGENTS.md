# AGENTS.md — Frontend Source

Last Updated: 2026-01-06
Applies To: `src/frontend/src/`

## Directory Structure

```
src/
├── api/              # API client modules
├── components/       # Reusable components
├── contexts/         # React contexts (state management)
├── pages/            # Page components (routes)
│   └── crm/          # CRM-specific pages
├── tracking/         # Analytics tracking utilities
├── App.tsx           # Root component with routing
├── main.tsx          # Application entry point
└── index.css         # Global styles
```

## API Directory (`api/`)

API client modules for each backend domain:

| File | Backend Endpoint |
|------|------------------|
| `client.ts` | Base axios client with interceptors |
| `auth.ts` | `/api/v1/auth/` |
| `clients.ts` | `/api/v1/clients/` |
| `crm.ts` | `/api/v1/crm/` |
| `projects.ts` | `/api/v1/projects/` |
| `documents.ts` | `/api/v1/documents/` |
| `calendar.ts` | `/api/v1/calendar/` |
| `automation.ts` | `/api/v1/automation/` |
| `tracking.ts` | `/api/v1/tracking/` |

## Components Directory (`components/`)

| Component | Purpose |
|-----------|---------|
| `Layout.tsx` | Main layout wrapper with nav |
| `ProtectedRoute.tsx` | Auth-required route wrapper |
| `ErrorBoundary.tsx` | Error handling wrapper |
| `LoadingSpinner.tsx` | Loading indicator |
| `ImpersonationBanner.tsx` | Break-glass warning |

## Contexts Directory (`contexts/`)

| Context | Purpose |
|---------|---------|
| `AuthContext.tsx` | Authentication state, login/logout |
| `ImpersonationContext.tsx` | Impersonation detection |

## Pages Directory (`pages/`)

Top-level pages:

| Page | Route | Purpose |
|------|-------|---------|
| `Dashboard.tsx` | `/dashboard` | Main dashboard |
| `Login.tsx` | `/login` | Login form |
| `Register.tsx` | `/register` | Registration |
| `Clients.tsx` | `/clients` | Client list |
| `Projects.tsx` | `/projects` | Project list |
| `Documents.tsx` | `/documents` | Document management |
| `CalendarSync.tsx` | `/calendar` | Calendar settings |
| `Automation.tsx` | `/automation` | Workflow list |
| `WorkflowBuilder.tsx` | `/workflow-builder/:id` | Visual workflow editor |

### CRM Pages (`pages/crm/`)

| Page | Route | Purpose |
|------|-------|---------|
| `Leads.tsx` | `/crm/leads` | Lead list |
| `Prospects.tsx` | `/crm/prospects` | Prospect list |
| `Deals.tsx` | `/crm/deals` | Deal list |
| `PipelineKanban.tsx` | `/crm/pipeline` | Kanban board |
| `DealAnalytics.tsx` | `/crm/analytics` | Deal analytics |
| `Campaigns.tsx` | `/crm/campaigns` | Campaign list |
| `ContactGraphView.tsx` | `/crm/graph` | Contact relationship graph |

## Common Patterns

### Data Fetching

```typescript
import { useQuery, useMutation } from '@tanstack/react-query'

// Fetch
const { data, isLoading } = useQuery({
  queryKey: ['clients'],
  queryFn: () => clientsApi.list(),
})

// Mutate
const mutation = useMutation({
  mutationFn: (data) => clientsApi.create(data),
  onSuccess: () => queryClient.invalidateQueries(['clients']),
})
```

### Form Handling

```typescript
const [formData, setFormData] = useState<FormType>({})

const handleSubmit = async (e: FormEvent) => {
  e.preventDefault()
  await mutation.mutateAsync(formData)
}
```

### Error Handling

```typescript
<ErrorBoundary fallback={<ErrorPage />}>
  <MyComponent />
</ErrorBoundary>
```

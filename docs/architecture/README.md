# UBOS System Architecture

This document provides a comprehensive overview of the UBOS (Unified Business Operating System) architecture, design decisions, and technical structure.

---

## 📋 Table of Contents

- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [System Architecture Diagrams](#system-architecture-diagrams)
- [Component Architecture](#component-architecture)
- [Data Architecture](#data-architecture)
- [Module Organization](#module-organization)
- [Technology Stack](#technology-stack)
- [Architectural Principles](#architectural-principles)
- [Integration Patterns](#integration-patterns)
- [Security Architecture](#security-architecture)
- [Scalability & Performance](#scalability--performance)
- [Related Documentation](#related-documentation)

---

## Overview

UBOS is an enterprise-grade, unified platform for service firms built with modern, scalable architecture:

- **Multi-Tenant SaaS** - Firm-scoped data isolation at database level
- **Domain-Driven Design** - Organized by business domains/bounded contexts
- **API-First** - RESTful API with OpenAPI specification
- **Modern Stack** - Django 4.2 backend, React 18 frontend
- **Security-First** - Authentication, authorization, and audit built-in
- **Cloud-Native** - Container-ready, stateless services

### Key Characteristics

| Aspect | Approach |
|--------|----------|
| **Architecture Style** | Modular Monolith (microservices-ready) |
| **Data Model** | Multi-tenant with firm-scoped isolation |
| **API Design** | RESTful with Django REST Framework |
| **Frontend** | SPA (Single Page Application) |
| **Authentication** | JWT with refresh tokens |
| **Authorization** | Role-based + object-level permissions |
| **Deployment** | Docker containers, PostgreSQL database |

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        Mobile[Mobile App - Future]
    end
    
    subgraph "Frontend - React SPA"
        React[React 18 + TypeScript]
        ReactQuery[TanStack React Query]
        Router[React Router]
        Forms[React Hook Form]
    end
    
    subgraph "API Gateway"
        Nginx[Nginx - Reverse Proxy]
    end
    
    subgraph "Backend - Django"
        API[Django REST Framework]
        Auth[JWT Authentication]
        Permissions[Authorization Layer]
        
        subgraph "Domain Modules"
            Core[Core - Users, Firms, Auth]
            CRM[CRM - Leads, Deals]
            Clients[Clients]
            Projects[Projects]
            Finance[Finance - Billing]
            Docs[Documents]
            Comms[Communications]
            Auto[Automation]
        end
    end
    
    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL 15)]
        S3[S3 - File Storage]
        Redis[(Redis - Cache)]
    end
    
    subgraph "External Services"
        Stripe[Stripe - Payments]
        SendGrid[SendGrid - Email]
        Sentry[Sentry - Monitoring]
    end
    
    Browser --> React
    Mobile -.-> React
    React --> ReactQuery
    ReactQuery --> Nginx
    Nginx --> API
    API --> Auth
    Auth --> Permissions
    Permissions --> Core
    Permissions --> CRM
    Permissions --> Clients
    Permissions --> Projects
    Permissions --> Finance
    Permissions --> Docs
    Permissions --> Comms
    Permissions --> Auto
    
    Core --> PostgreSQL
    CRM --> PostgreSQL
    Clients --> PostgreSQL
    Projects --> PostgreSQL
    Finance --> PostgreSQL
    Finance --> Stripe
    Docs --> S3
    Docs --> PostgreSQL
    Comms --> SendGrid
    Auto --> PostgreSQL
    
    API --> Redis
    API --> Sentry
```

---

## System Architecture Diagrams

### Request Flow

```mermaid
sequenceDiagram
    participant U as User Browser
    participant F as React Frontend
    participant N as Nginx
    participant D as Django API
    participant A as Auth Middleware
    participant P as Permissions
    participant M as Module (e.g., CRM)
    participant DB as PostgreSQL
    
    U->>F: User Action
    F->>F: React Query Hook
    F->>N: HTTP Request (with JWT)
    N->>D: Forward to Django
    D->>A: Authenticate JWT
    A->>A: Verify Token
    A->>P: Check Permissions
    P->>P: Verify Firm Scope
    P->>M: Execute Business Logic
    M->>DB: Query (firm-scoped)
    DB-->>M: Data
    M-->>P: Response
    P-->>D: Authorized Response
    D-->>N: JSON Response
    N-->>F: HTTP Response
    F->>F: Update React Query Cache
    F-->>U: UI Update
```

### Multi-Tenancy Architecture

```mermaid
graph TB
    subgraph "Firm A"
        UserA1[User A1]
        UserA2[User A2]
        DataA[(Firm A Data)]
    end
    
    subgraph "Firm B"
        UserB1[User B1]
        UserB2[User B2]
        DataB[(Firm B Data)]
    end
    
    subgraph "Application Layer"
        API[Django API]
        FirmMiddleware[Firm Scope Middleware]
    end
    
    subgraph "Database"
        SharedDB[(PostgreSQL)]
        FirmARecords[Firm A Records - firm_id=1]
        FirmBRecords[Firm B Records - firm_id=2]
    end
    
    UserA1 --> API
    UserA2 --> API
    UserB1 --> API
    UserB2 --> API
    
    API --> FirmMiddleware
    FirmMiddleware --> SharedDB
    
    SharedDB --> FirmARecords
    SharedDB --> FirmBRecords
    
    FirmARecords -.Filter firm_id=1.-> DataA
    FirmBRecords -.Filter firm_id=2.-> DataB
```

---

## Component Architecture

### Backend - Django Modules

```
backend/
├── config/              # Django settings and configuration
│   ├── settings.py     # Base settings
│   ├── urls.py         # Root URL configuration
│   └── wsgi.py         # WSGI application
│
└── modules/            # Domain modules (Django apps)
    ├── core/           # Infrastructure
    │   ├── models.py   # User, Firm, base models
    │   ├── auth.py     # JWT authentication
    │   ├── permissions.py
    │   └── middleware.py
    │
    ├── crm/            # Customer Relationship Management
    │   ├── models.py   # Lead, Prospect, Deal, Pipeline
    │   ├── serializers.py
    │   ├── views.py
    │   └── services.py # Business logic
    │
    ├── clients/        # Client Management
    │   ├── models.py   # Client, Contact
    │   ├── views.py
    │   └── portal.py   # Client portal logic
    │
    ├── projects/       # Project Delivery
    │   ├── models.py   # Project, Task, TimeEntry
    │   └── views.py
    │
    ├── finance/        # Billing & Invoicing
    │   ├── models.py   # Invoice, Payment
    │   ├── stripe.py   # Stripe integration
    │   └── views.py
    │
    ├── documents/      # Document Management
    │   ├── models.py   # Document, Version
    │   ├── storage.py  # S3 integration
    │   └── views.py
    │
    ├── communications/ # Messaging
    │   ├── models.py   # Message, Conversation
    │   └── views.py
    │
    └── automation/     # Workflows
        ├── models.py   # Workflow, Trigger, Action
        ├── engine.py   # Workflow execution
        └── views.py
```

### Frontend - React Structure

```
frontend/src/
├── api/                # API client layer
│   ├── client.ts      # Axios instance with auth
│   ├── auth.ts        # Auth API + hooks
│   ├── crm.ts         # CRM API + hooks
│   ├── clients.ts     # Clients API + hooks
│   └── [module].ts    # Other modules
│
├── pages/              # Route-level components
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   ├── Clients.tsx
│   ├── crm/
│   │   ├── Deals.tsx
│   │   ├── Leads.tsx
│   │   └── PipelineKanban.tsx
│   └── [feature]/
│
├── components/         # Reusable UI components
│   ├── Sidebar.tsx
│   ├── LoadingSpinner.tsx
│   ├── ErrorBoundary.tsx
│   └── [component].tsx
│
├── hooks/              # Custom React hooks
│   ├── useAuth.ts
│   └── [hook].ts
│
├── types/              # TypeScript definitions
│   └── index.ts
│
├── utils/              # Utility functions
│   └── helpers.ts
│
├── App.tsx             # Root component + routing
└── main.tsx            # Application entry point
```

---

## Data Architecture

### Multi-Tenant Data Model

Every table in the database has a `firm_id` foreign key that links to the `core_firm` table. This ensures complete data isolation between tenants.

```mermaid
erDiagram
    Firm ||--o{ User : "has"
    Firm ||--o{ Client : "has"
    Firm ||--o{ Deal : "has"
    Firm ||--o{ Project : "has"
    Firm ||--o{ Invoice : "has"
    
    Firm {
        int id PK
        string name
        string slug
        boolean is_active
        timestamp created_at
    }
    
    User {
        int id PK
        int firm_id FK
        string email
        string role
        boolean is_active
    }
    
    Client {
        int id PK
        int firm_id FK
        string name
        string type
    }
    
    Deal {
        int id PK
        int firm_id FK
        int pipeline_id FK
        int stage_id FK
        decimal value
        int probability
    }
```

### Core Domain Models

```mermaid
graph TB
    subgraph "Core Module"
        Firm[Firm]
        User[User]
    end
    
    subgraph "CRM Module"
        Lead[Lead]
        Prospect[Prospect]
        Pipeline[Pipeline]
        Stage[Pipeline Stage]
        Deal[Deal]
        Campaign[Campaign]
    end
    
    subgraph "Clients Module"
        Client[Client]
        Contact[Contact]
        Contract[Contract]
    end
    
    subgraph "Projects Module"
        Project[Project]
        Task[Task]
        TimeEntry[Time Entry]
    end
    
    subgraph "Finance Module"
        Invoice[Invoice]
        Payment[Payment]
        LineItem[Line Item]
    end
    
    Firm --> User
    Firm --> Lead
    Firm --> Client
    Firm --> Project
    Firm --> Invoice
    
    Lead --> Prospect
    Prospect --> Deal
    Deal --> Pipeline
    Deal --> Stage
    Deal --> Campaign
    Deal --> Client
    
    Client --> Contact
    Client --> Contract
    Client --> Project
    
    Project --> Task
    Task --> TimeEntry
    TimeEntry --> User
    
    Project --> Invoice
    Invoice --> Payment
    Invoice --> LineItem
```

---

## Module Organization

UBOS follows **Domain-Driven Design** principles with modules organized by business domain (bounded contexts):

### Module Ownership & Boundaries

| Module | Responsibility | Dependencies |
|--------|---------------|--------------|
| **core** | Infrastructure: Auth, Firms, Users | None (foundational) |
| **crm** | Sales pipeline: Leads → Deals | core |
| **clients** | Client relationships, portal | core, crm (optional) |
| **projects** | Project delivery, tasks, time | core, clients |
| **finance** | Billing, invoicing, payments | core, clients, projects |
| **documents** | Document storage, versioning | core, projects (optional) |
| **communications** | Messaging, conversations | core, clients |
| **automation** | Workflows, triggers, actions | core, all modules |
| **calendar** | Scheduling, events | core, clients |
| **support** | Ticketing, SLA management | core, clients |

### Module Interaction Rules

1. **Core → No dependencies** - Foundation for all modules
2. **Business modules → Core only** - Depend on core infrastructure
3. **Cross-module communication** - Through well-defined APIs (requires ADR)
4. **Automation module** - Can integrate with all modules (observer pattern)

---

## Technology Stack

### Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Primary language |
| **Django** | 4.2 LTS | Web framework |
| **Django REST Framework** | 3.14+ | API framework |
| **PostgreSQL** | 15+ | Primary database |
| **Redis** | 7+ | Caching & sessions |
| **Celery** | 5.3+ | Async tasks (future) |
| **pytest** | 7.4+ | Testing framework |

### Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.3+ | UI library |
| **TypeScript** | 5.9+ | Type safety |
| **Vite** | 5.4+ | Build tool |
| **TanStack React Query** | 5.x | Data fetching & caching |
| **React Hook Form** | 7.x | Form management |
| **React Router** | 6.x | Client-side routing |
| **Vitest** | 1.x | Testing framework |
| **Playwright** | 1.x | E2E testing |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Nginx** | Reverse proxy |
| **GitHub Actions** | CI/CD |
| **AWS S3** | File storage |
| **Sentry** | Error tracking |
| **Stripe** | Payment processing |

---

## Architectural Principles

### 1. Multi-Tenancy
- **Firm-scoped isolation** at database level
- All tables have `firm_id` foreign key
- Queries automatically filtered by firm
- No cross-firm data access

### 2. Domain-Driven Design
- Modules organized by business domain
- Clear bounded contexts
- Ubiquitous language within modules
- Well-defined module boundaries

### 3. API-First Design
- RESTful API as primary interface
- OpenAPI specification (Swagger)
- Versioning strategy for breaking changes
- Consistent response formats

### 4. Security-First
- Authentication on every request
- Authorization checks at API and object level
- Input validation using serializers
- Audit logging for sensitive operations
- Secret management via environment variables

### 5. Scalability
- Stateless API services (scale horizontally)
- Database connection pooling
- Caching with Redis
- Async tasks with Celery (future)
- CDN for static assets

### 6. Performance
- Database query optimization (select_related, prefetch_related)
- API response caching
- Frontend code splitting
- React Query for client-side caching
- Pagination for large datasets

### 7. Maintainability
- Clear separation of concerns
- Comprehensive test coverage (80%+ backend, 60%+ frontend)
- Documentation as code
- Consistent code style (Black, Prettier, ESLint)
- Type safety (Python type hints, TypeScript)

---

## Integration Patterns

### External Service Integration

```mermaid
graph LR
    subgraph "UBOS Backend"
        API[Django API]
        Finance[Finance Module]
        Comms[Communications]
        Docs[Documents]
    end
    
    subgraph "External Services"
        Stripe[Stripe API]
        SendGrid[SendGrid API]
        S3[AWS S3]
        Sentry[Sentry]
    end
    
    Finance -->|Payment Processing| Stripe
    Comms -->|Email Delivery| SendGrid
    Docs -->|File Storage| S3
    API -->|Error Tracking| Sentry
```

### Frontend-Backend Communication

- **Protocol**: HTTP/HTTPS (REST)
- **Format**: JSON
- **Authentication**: JWT Bearer tokens
- **Caching**: React Query on frontend, Redis on backend
- **Error Handling**: Standardized error responses

---

## Security Architecture

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as Auth API
    participant DB as Database
    
    U->>F: Login (email, password)
    F->>A: POST /api/auth/login
    A->>DB: Verify credentials
    DB-->>A: User + Firm
    A->>A: Generate JWT + Refresh Token
    A-->>F: { access_token, refresh_token, user }
    F->>F: Store tokens in localStorage
    F-->>U: Redirect to Dashboard
    
    Note over F: For subsequent requests
    F->>A: API Request (Authorization: Bearer <token>)
    A->>A: Verify JWT
    A-->>F: Protected Resource
```

### Authorization Layers

1. **Authentication**: JWT token verification
2. **Firm Scope**: Automatic filtering by user's firm
3. **Role-Based**: User roles (admin, manager, member)
4. **Object-Level**: Ownership and custom permissions
5. **Action-Level**: CRUD permissions per model

---

## Scalability & Performance

### Current Architecture (v0.1.0)
- **Single Django instance** behind Nginx
- **PostgreSQL** on separate container
- **Redis** for session and cache
- **S3** for file storage

### Future Scaling Path

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx / ALB]
    end
    
    subgraph "Application Tier - Multiple Instances"
        Django1[Django Instance 1]
        Django2[Django Instance 2]
        Django3[Django Instance N]
    end
    
    subgraph "Cache Layer"
        Redis[Redis Cluster]
    end
    
    subgraph "Data Tier"
        PG[PostgreSQL Primary]
        PGR[PostgreSQL Replicas]
    end
    
    subgraph "Storage"
        S3[S3 / CloudFront CDN]
    end
    
    LB --> Django1
    LB --> Django2
    LB --> Django3
    
    Django1 --> Redis
    Django2 --> Redis
    Django3 --> Redis
    
    Django1 --> PG
    Django2 --> PG
    Django3 --> PG
    
    PG --> PGR
    
    Django1 --> S3
    Django2 --> S3
    Django3 --> S3
```

### Performance Targets

| Metric | Target | Current Status |
|--------|--------|----------------|
| **API Response Time** | < 200ms (p95) | ✅ Meeting |
| **Database Query Time** | < 50ms (p95) | ✅ Meeting |
| **Frontend Load Time** | < 2s (LCP) | ✅ Meeting |
| **Concurrent Users** | 1000+ per instance | ✅ Meeting |
| **Database Connections** | 100 per instance | ✅ Meeting |

---

## Related Documentation

### Architecture Deep-Dives
- [Module Documentation](modules/README.md) - Detailed module documentation
- [Data Models](data-models/README.md) - Database schema and relationships
- [Design Decisions](decisions/README.md) - ADRs for key technical decisions

### Development & Operations
- [Development Guide](../development/README.md) - Development setup and practices
- [API Reference](../reference/api/) - API endpoint documentation
- [Operations](../operations/README.md) - Deployment and operations guide
- [Security](../security/README.md) - Security policies and procedures

### Product Context
- [PRODUCT.md](../../PRODUCT.md) - Product vision and business context
- [README.md](../../README.md) - Project overview
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Contribution guidelines

---

**Last Updated**: 2026-01-24  
**Document Version**: 2.0  
**Status**: Active - Comprehensive

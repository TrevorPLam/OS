# AI Agent Instructions - OS

## Repository Overview
This is a full-stack application with a Python Django backend and React frontend.

## Architecture
- **Backend**: Python Django REST Framework
- **Frontend**: React with Vite
- **Structure**: Separate backend/ and frontend/ directories

## Key Conventions
- Backend modules in `backend/modules/` organized by domain
- API endpoints in `backend/api/` organized by feature
- Frontend features in `frontend/features/`
- Frontend components in `frontend/components/`

## Common Tasks
- **Backend module**: Create in `backend/modules/[module-name]/` with models, views, serializers
- **API endpoint**: Create in `backend/api/[feature]/` with views.py and urls.py
- **Frontend feature**: Create in `frontend/features/[feature-name]/`
- **Frontend component**: Add to `frontend/components/` if reusable

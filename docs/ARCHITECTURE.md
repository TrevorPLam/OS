# Architecture

## Overview

- Backend: Django app in `backend/` exposing APIs and business logic.
- Frontend: `Vite`/React app in `frontend/` consuming the API.
- Tests: shared test suites in `tests/` and app-specific tests in each app.

## High-level flow

1. Client interacts with the frontend.
2. Frontend calls backend APIs.
3. Backend handles domain logic and data persistence.

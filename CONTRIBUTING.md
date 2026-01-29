# Contributing

Thank you for your interest in contributing to OS! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** (if you don't have direct access)
2. **Clone your fork** or the main repository
3. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Frontend (React)

1. **Install dependencies:**
   ```bash
   pnpm install
   ```

2. **Run the development server:**
   ```bash
   pnpm dev
   ```

### Backend (Python/Django)

1. **Navigate to the backend directory:**
   ```bash
   cd services/api-service/backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## Making Changes

### Code Style

- **Frontend:** Follow TypeScript/React best practices
- **Backend:** Follow PEP 8 Python style guide
- Run linters before committing:
  ```bash
  # Frontend
  pnpm lint
  pnpm type-check
  
  # Backend
  flake8 .  # If configured
  ```

### Project Structure

- **Apps** (`apps/`) - React frontend application
- **Services** (`services/api-service/`) - Django backend API
- **Packages** (`packages/`) - Shared UI components and utilities
- **Infrastructure** (`infrastructure/`) - Deployment and infrastructure configs

## Pull Request Process

1. **Ensure your code builds:**
   ```bash
   # Frontend
   pnpm build
   pnpm lint
   pnpm type-check
   
   # Backend
   python manage.py check
   ```

2. **Update documentation** if you've changed functionality

3. **Create a pull request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots (if UI changes)

4. **Get approval** from code owners (see CODEOWNERS file)

5. **Ensure CI checks pass** before requesting review

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- Include:
  - Clear description of the issue
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Node/Python version, etc.)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Questions?

If you have questions, please open an issue or contact the maintainers listed in CODEOWNERS.

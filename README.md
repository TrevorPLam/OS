# OS

Operating system for professional services with React frontend and Django backend.

## Installation

### Frontend

```bash
# Install dependencies
pnpm install
```

### Backend

```bash
# Navigate to backend directory
cd services/api-service/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt

# Run migrations
python manage.py migrate
```

## Usage

### Frontend

```bash
# Run development server
pnpm dev

# Build
pnpm build

# Run linter
pnpm lint

# Type check
pnpm type-check
```

### Backend

```bash
# Run development server
python manage.py runserver

# Run Django checks
python manage.py check
```

## Project Structure

- `apps/web/` - React frontend application
- `services/api-service/` - Django REST API backend
- `packages/ui/` - Shared design system components
- `packages/utils/` - Shared utilities
- `infrastructure/` - Deployment and infrastructure configs
- `docs/` - Documentation

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

Proprietary - See [LICENSE](LICENSE) for details.

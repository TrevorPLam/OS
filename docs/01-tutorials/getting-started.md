# Getting Started with ConsultantPro

This tutorial will guide you through setting up ConsultantPro for local development.

## Prerequisites

Before you begin, ensure you have:
- **Python 3.11+** installed
- **PostgreSQL 15+** installed and running
- **Node.js 16+** (for frontend development)
- **Git** for version control

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/consultantpro.git
cd consultantpro
```

## Step 2: Set Up Python Environment

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your local settings:

```bash
# Django Settings
DJANGO_SECRET_KEY="dev-secret-key-change-in-production"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=consultantpro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# CORS (for local frontend)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# AWS S3 (Optional - for document storage)
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
# AWS_STORAGE_BUCKET_NAME=your-bucket

# Stripe (Optional - for payment processing)
# STRIPE_SECRET_KEY=sk_test_your-key
# STRIPE_PUBLISHABLE_KEY=pk_test_your-key
```

## Step 4: Set Up Database

Create the database:

```bash
createdb consultantpro
```

Run migrations:

```bash
cd src
python manage.py migrate
```

Create a superuser account:

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

## Step 5: Run the Development Server

Start the Django development server:

```bash
python manage.py runserver 0.0.0.0:8000
```

The API will be available at:
- **API Root:** http://localhost:8000/api/
- **Swagger Docs:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **Admin Panel:** http://localhost:8000/admin/

## Step 6: Verify Installation

### Check System Status

```bash
python manage.py check
```

You should see: "System check identified no issues"

### Run Tests

```bash
cd ..  # Back to project root
pytest
```

All tests should pass.

## Step 7: Set Up Frontend (Optional)

If you're working on the frontend:

```bash
cd src/frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

## Using Docker (Alternative Setup)

If you prefer Docker:

```bash
docker compose up --build
```

This will:
- Start PostgreSQL
- Start Django backend on http://localhost:8000
- Start frontend on http://localhost:3000

## Next Steps

Now that you have ConsultantPro running:

1. **Explore the API** - Visit http://localhost:8000/api/docs/ for interactive API documentation
2. **Read the API Guide** - See [API Usage Guide](../03-reference/api-usage.md) for endpoint details
3. **Understand the Architecture** - See [Architecture Overview](../04-explanation/architecture-overview.md) for system design
4. **Learn the Tier System** - See [Tier System Reference](../03-reference/tier-system.md) for governance model
5. **Start Contributing** - See [Contributing Guide](../../CONTRIBUTING.md) for development workflow

## Troubleshooting

### Database Connection Issues

If you get "connection refused" errors:

1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql  # Linux
   brew services list                # macOS
   ```

2. Check your database credentials in `.env`

3. Ensure the database exists:
   ```bash
   psql -l | grep consultantpro
   ```

### Migration Issues

If migrations fail:

1. Drop and recreate the database:
   ```bash
   dropdb consultantpro
   createdb consultantpro
   python manage.py migrate
   ```

2. Check for pending migrations:
   ```bash
   python manage.py showmigrations
   ```

### Port Already in Use

If port 8000 is already in use:

```bash
# Find the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
python manage.py runserver 8001
```

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/en/4.2/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Getting Help

- **Documentation:** [docs/README.md](../README.md)
- **Issues:** GitHub Issues
- **Security:** See [SECURITY.md](../../SECURITY.md)

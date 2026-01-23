#!/bin/bash
# Database Migration Script for UBOS
# Run this after Phase 1 architectural refactor

set -e

echo "=========================================="
echo "UBOS - Database Migration Setup"
echo "=========================================="
echo ""
echo "This script creates and applies migrations for:"
echo "  - CRM Module (Leads, Prospects, Campaigns, Proposals, Contracts)"
echo "  - Clients Module (Client, ClientPortalUser, ClientNote, ClientEngagement)"
echo "  - Updated foreign keys (Projects, Documents, Finance)"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start database
echo "📦 Starting PostgreSQL database..."
docker-compose up -d db
sleep 5
echo "✅ Database started"
echo ""

# Create migrations
echo "🔨 Creating migrations..."
docker-compose run --rm web python manage.py makemigrations

echo ""
echo "✅ Migrations created successfully!"
echo ""

# Show migration plan
echo "📋 Migration plan:"
docker-compose run --rm web python manage.py showmigrations

echo ""
read -p "Apply these migrations? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⚙️  Applying migrations..."
    docker-compose run --rm web python manage.py migrate

    echo ""
    echo "✅ Migrations applied successfully!"
    echo ""

    # Create superuser prompt
    read -p "Create a superuser for Django admin? (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose run --rm web python manage.py createsuperuser
    fi
else
    echo "⏸️  Migration cancelled. Run './scripts/migrate.sh' again when ready."
    exit 0
fi

echo ""
echo "=========================================="
echo "✅ Database setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start the development server:"
echo "     docker-compose up"
echo ""
echo "  2. Access Django admin:"
echo "     http://localhost:8000/admin"
echo ""
echo "  3. Access API documentation:"
echo "     http://localhost:8000/api/docs/"
echo ""
echo "Available API endpoints:"
echo "  - /api/crm/leads/"
echo "  - /api/crm/prospects/"
echo "  - /api/crm/campaigns/"
echo "  - /api/crm/proposals/"
echo "  - /api/crm/contracts/"
echo "  - /api/clients/clients/"
echo "  - /api/clients/portal-users/"
echo "  - /api/clients/notes/"
echo "  - /api/clients/engagements/"
echo "  - /api/projects/projects/"
echo "  - /api/finance/invoices/"
echo "  - /api/documents/folders/"
echo "  - /api/assets/assets/"
echo ""

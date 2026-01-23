#!/bin/bash
#
# Database Migrations Setup Script
# Run this after Docker is installed to create initial migrations
#

set -e

echo "========================================="
echo "UBOS - Database Migrations Setup"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Please install Docker and Docker Compose first."
    echo "See: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed."
    echo "Please install Docker Compose first."
    echo "See: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "Step 1: Starting PostgreSQL database..."
docker-compose up -d db

echo ""
echo "Step 2: Waiting for database to be ready..."
sleep 5

echo ""
echo "Step 3: Building web container with updated requirements..."
docker-compose build web

echo ""
echo "Step 4: Creating database migrations for all modules..."
docker-compose run --rm web python manage.py makemigrations crm
docker-compose run --rm web python manage.py makemigrations projects
docker-compose run --rm web python manage.py makemigrations finance
docker-compose run --rm web python manage.py makemigrations documents
docker-compose run --rm web python manage.py makemigrations assets

echo ""
echo "Step 5: Applying migrations to database..."
docker-compose run --rm web python manage.py migrate

echo ""
echo "Step 6: Creating superuser (admin account)..."
echo "You'll be prompted to enter username, email, and password:"
docker-compose run --rm web python manage.py createsuperuser

echo ""
echo "========================================="
echo "✓ Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Start the application:"
echo "   docker-compose up"
echo ""
echo "2. Access Django admin:"
echo "   http://localhost:8000/admin/"
echo ""
echo "3. Access API documentation:"
echo "   http://localhost:8000/api/docs/"
echo ""
echo "4. Install frontend dependencies:"
echo "   cd frontend && npm install && npm run dev"
echo ""

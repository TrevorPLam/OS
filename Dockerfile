# Dockerfile for ConsultantPro Django Application
# Python 3.11+ on Debian-based image

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY src/ /app/src/

# Create directories for static and media files
RUN mkdir -p /app/src/staticfiles /app/src/media

# Expose port 8000
EXPOSE 8000

# Set working directory to src
WORKDIR /app/src

# Run production server with gunicorn
# SECURITY: Do not use Django's development server in production
# - No SSL/TLS support
# - Single-threaded (poor performance)
# - DEBUG mode leaks stack traces
# - Not hardened for security
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "config.wsgi:application"]

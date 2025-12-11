# Dockerfile for django-cities testing
# Supports multiple Python versions via build args

ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

# Install system dependencies for PostgreSQL, MySQL, and PostGIS
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    default-libmysqlclient-dev \
    pkg-config \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install Python dependencies
# The Django version will be specified via pip install command
RUN pip install --upgrade pip setuptools wheel

# Install the package in development mode
RUN pip install -e .

# Install test dependencies
RUN pip install psycopg[binary]>=3.0

# Default command runs tests
CMD ["python", "test_project/manage.py", "test", "test_app", "--noinput"]

# Django Cities - Test Commands
# Run `just --list` to see all available commands

# Default recipe - shows help
default:
    @just --list

# Run PostgreSQL tests with Python 3.14 + Django 6.0 (quickest test with latest versions)
test-postgres-quick:
    @echo "Running quick PostgreSQL test (Python 3.14 + Django 6.0)..."
    docker compose up --build --exit-code-from test-py314-django60 test-py314-django60

# Run all PostgreSQL test combinations across Python 3.12, 3.13, 3.14 and Django 5.0, 5.1, 5.2, 6.0
test-postgres-all:
    @echo "Running all PostgreSQL test combinations..."
    @echo "Testing Python 3.12 + Django 5.0..."
    docker compose up --build --exit-code-from test-py312-django50 test-py312-django50
    @echo "Testing Python 3.12 + Django 5.1..."
    docker compose up --build --exit-code-from test-py312-django51 test-py312-django51
    @echo "Testing Python 3.12 + Django 5.2..."
    docker compose up --build --exit-code-from test-py312-django52 test-py312-django52
    @echo "Testing Python 3.12 + Django 6.0..."
    docker compose up --build --exit-code-from test-py312-django60 test-py312-django60
    @echo "Testing Python 3.13 + Django 5.1..."
    docker compose up --build --exit-code-from test-py313-django51 test-py313-django51
    @echo "Testing Python 3.13 + Django 5.2..."
    docker compose up --build --exit-code-from test-py313-django52 test-py313-django52
    @echo "Testing Python 3.13 + Django 6.0..."
    docker compose up --build --exit-code-from test-py313-django60 test-py313-django60
    @echo "Testing Python 3.14 + Django 5.2..."
    docker compose up --build --exit-code-from test-py314-django52 test-py314-django52
    @echo "Testing Python 3.14 + Django 6.0..."
    docker compose up --build --exit-code-from test-py314-django60 test-py314-django60

# Run PostgreSQL tests for specific Python and Django version (e.g., just test-postgres 3.13 5.1)
test-postgres py dj:
    #!/bin/bash
    PY_VER=$(echo "{{py}}" | tr -d '.')
    DJ_VER=$(echo "{{dj}}" | tr -d '.')
    echo "Running PostgreSQL tests (Python {{py}} + Django {{dj}})..."
    docker compose up --build --exit-code-from test-py${PY_VER}-django${DJ_VER} test-py${PY_VER}-django${DJ_VER}

# Run MySQL tests with Python 3.14 + Django 6.0 (quickest test with latest versions)
test-mysql-quick:
    @echo "Running quick MySQL test (Python 3.14 + Django 6.0)..."
    docker compose up --build --exit-code-from test-py314-django60-mysql test-py314-django60-mysql

# Run all MySQL test combinations
test-mysql-all:
    @echo "Running all MySQL test combinations..."
    @echo "Testing Python 3.12 + Django 5.2 (MySQL)..."
    docker compose up --build --exit-code-from test-py312-django52-mysql test-py312-django52-mysql
    @echo "Testing Python 3.13 + Django 6.0 (MySQL)..."
    docker compose up --build --exit-code-from test-py313-django60-mysql test-py313-django60-mysql
    @echo "Testing Python 3.14 + Django 6.0 (MySQL)..."
    docker compose up --build --exit-code-from test-py314-django60-mysql test-py314-django60-mysql

# Run MySQL tests for specific Python and Django version (e.g., just test-mysql 3.14 6.0)
test-mysql py dj:
    #!/bin/bash
    PY_VER=$(echo "{{py}}" | tr -d '.')
    DJ_VER=$(echo "{{dj}}" | tr -d '.')
    echo "Running MySQL tests (Python {{py}} + Django {{dj}})..."
    docker compose up --build --exit-code-from test-py${PY_VER}-django${DJ_VER}-mysql test-py${PY_VER}-django${DJ_VER}-mysql

# Run quick test on both PostgreSQL and MySQL
test-both-dbs:
    @echo "Running quick test on both databases..."
    just test-postgres-quick
    just test-mysql-quick

# Run all tests on both PostgreSQL and MySQL
test-both-dbs-all:
    @echo "Running all tests on both PostgreSQL and MySQL..."
    @echo ""
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "PostgreSQL Tests"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    just test-postgres-all
    @echo ""
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "MySQL Tests"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    just test-mysql-all

# Build Docker images
build:
    @echo "Building Docker images..."
    docker compose build

# Start the PostgreSQL database service
db:
    @echo "Starting PostgreSQL database..."
    docker compose up -d db
    @echo "Waiting for database to be ready..."
    @sleep 5
    @echo "Database is ready!"

# Start the MySQL database service
db-mysql:
    @echo "Starting MySQL database..."
    docker compose up -d mysql
    @echo "Waiting for database to be ready..."
    @sleep 10
    @echo "MySQL is ready!"

# Start both database services
db-all:
    @echo "Starting PostgreSQL and MySQL databases..."
    docker compose up -d db mysql
    @echo "Waiting for databases to be ready..."
    @sleep 10
    @echo "Databases are ready!"

# Open a Python shell in the test environment
shell:
    docker compose run --rm test-py314-django60 bash

# Open a PostgreSQL shell
db-shell:
    docker compose exec db psql -U postgres -d django_cities

# Open a MySQL shell
db-shell-mysql:
    docker compose exec mysql mysql -u django -pdjango django_cities

# Stop containers and remove volumes
clean:
    @echo "Stopping containers and removing volumes..."
    docker compose down -v

# Remove all containers, volumes, and images
clean-all:
    @echo "Removing all containers, volumes, and images..."
    docker compose down -v --rmi all

# Run ruff linter (checks code quality)
lint:
    @echo "Running ruff linter..."
    ruff check cities/

# Run ruff linter with auto-fix
lint-fix:
    @echo "Running ruff linter with auto-fix..."
    ruff check --fix cities/

# Format code with ruff
format:
    @echo "Formatting code with ruff..."
    ruff format cities/ test_project/

# Check code formatting without making changes
format-check:
    @echo "Checking code format..."
    ruff format --check cities/ test_project/

# Install pre-commit hooks
pre-commit-install:
    @echo "Installing pre-commit hooks..."
    pre-commit install

# Run pre-commit hooks on all files
pre-commit:
    @echo "Running pre-commit hooks on all files..."
    pre-commit run --all-files

# Update pre-commit hooks to latest versions
pre-commit-update:
    @echo "Updating pre-commit hooks..."
    pre-commit autoupdate

# Run a specific test file (e.g., just test-file test_models)
test-file file:
    docker compose run --rm test-py314-django60 sh -c "\
        pip install 'Django>=6.0,<6.1' && \
        python test_project/manage.py migrate --noinput && \
        python test_project/manage.py test test_app.tests.{{file}} --noinput -v 2"

# Show database logs
logs-db:
    docker compose logs -f db

# Show MySQL database logs
logs-db-mysql:
    docker compose logs -f mysql

# Show all running containers
ps:
    docker compose ps

# Run PostgreSQL tests for Python 3.12 with all Django versions
test-postgres-py312:
    @echo "Testing PostgreSQL with Python 3.12 (all Django versions)..."
    docker compose up --build --exit-code-from test-py312-django50 test-py312-django50
    docker compose up --build --exit-code-from test-py312-django51 test-py312-django51
    docker compose up --build --exit-code-from test-py312-django52 test-py312-django52
    docker compose up --build --exit-code-from test-py312-django60 test-py312-django60

# Run PostgreSQL tests for Python 3.13 with all Django versions
test-postgres-py313:
    @echo "Testing PostgreSQL with Python 3.13 (all Django versions)..."
    docker compose up --build --exit-code-from test-py313-django51 test-py313-django51
    docker compose up --build --exit-code-from test-py313-django52 test-py313-django52
    docker compose up --build --exit-code-from test-py313-django60 test-py313-django60

# Run PostgreSQL tests for Python 3.14 with all Django versions
test-postgres-py314:
    @echo "Testing PostgreSQL with Python 3.14 (all Django versions)..."
    docker compose up --build --exit-code-from test-py314-django52 test-py314-django52
    docker compose up --build --exit-code-from test-py314-django60 test-py314-django60

# Run PostgreSQL tests for Django 5.0 with all Python versions
test-postgres-django50:
    @echo "Testing PostgreSQL with Django 5.0 (all Python versions)..."
    docker compose up --build --exit-code-from test-py312-django50 test-py312-django50

# Run PostgreSQL tests for Django 5.1 with all Python versions
test-postgres-django51:
    @echo "Testing PostgreSQL with Django 5.1 (all Python versions)..."
    docker compose up --build --exit-code-from test-py312-django51 test-py312-django51
    docker compose up --build --exit-code-from test-py313-django51 test-py313-django51

# Run PostgreSQL tests for Django 5.2 with all Python versions
test-postgres-django52:
    @echo "Testing PostgreSQL with Django 5.2 (all Python versions)..."
    docker compose up --build --exit-code-from test-py312-django52 test-py312-django52
    docker compose up --build --exit-code-from test-py313-django52 test-py313-django52
    docker compose up --build --exit-code-from test-py314-django52 test-py314-django52

# Run PostgreSQL tests for Django 6.0 with all Python versions
test-postgres-django60:
    @echo "Testing PostgreSQL with Django 6.0 (all Python versions)..."
    docker compose up --build --exit-code-from test-py312-django60 test-py312-django60
    docker compose up --build --exit-code-from test-py313-django60 test-py313-django60
    docker compose up --build --exit-code-from test-py314-django60 test-py314-django60

# Show environment info
info:
    @echo "Docker version:"
    @docker --version
    @echo ""
    @echo "Docker Compose version:"
    @docker compose version
    @echo ""
    @echo "Available test services:"
    @docker compose config --services | grep "^test-"

# Django Cities - Test Commands
# Run `just --list` to see all available commands

# Default recipe - shows help
default:
    @just --list

# Run tests with Python 3.14 + Django 6.0 (quickest test with latest versions)
test-quick:
    @echo "Running quick test (Python 3.14 + Django 6.0)..."
    ./run-tests.sh 3.14 6.0

# Run all test combinations across Python 3.12, 3.13, 3.14 and Django 5.0, 5.1, 5.2, 6.0
test-all:
    ./run-tests.sh all

# Run tests for specific Python and Django version (e.g., just test 3.13 5.1)
test py dj:
    ./run-tests.sh {{py}} {{dj}}

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

# Open a Python shell in the test environment
shell:
    docker compose run --rm test-py314-django60 bash

# Open a PostgreSQL shell
db-shell:
    docker compose exec db psql -U postgres -d django_cities

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

# Show all running containers
ps:
    docker compose ps

# Run tests for Python 3.12 with all Django versions
test-py312:
    @echo "Testing Python 3.12 with all Django versions..."
    ./run-tests.sh 3.12 5.0
    ./run-tests.sh 3.12 5.1
    ./run-tests.sh 3.12 5.2
    ./run-tests.sh 3.12 6.0

# Run tests for Python 3.13 with all Django versions
test-py313:
    @echo "Testing Python 3.13 with all Django versions..."
    ./run-tests.sh 3.13 5.1
    ./run-tests.sh 3.13 5.2
    ./run-tests.sh 3.13 6.0

# Run tests for Python 3.14 with all Django versions
test-py314:
    @echo "Testing Python 3.14 with all Django versions..."
    ./run-tests.sh 3.14 5.2
    ./run-tests.sh 3.14 6.0

# Run tests for Django 5.0 with all Python versions
test-django50:
    @echo "Testing Django 5.0 with all Python versions..."
    ./run-tests.sh 3.12 5.0

# Run tests for Django 5.1 with all Python versions
test-django51:
    @echo "Testing Django 5.1 with all Python versions..."
    ./run-tests.sh 3.12 5.1
    ./run-tests.sh 3.13 5.1

# Run tests for Django 5.2 with all Python versions
test-django52:
    @echo "Testing Django 5.2 with all Python versions..."
    ./run-tests.sh 3.12 5.2
    ./run-tests.sh 3.13 5.2
    ./run-tests.sh 3.14 5.2

# Run tests for Django 6.0 with all Python versions
test-django60:
    @echo "Testing Django 6.0 with all Python versions..."
    ./run-tests.sh 3.12 6.0
    ./run-tests.sh 3.13 6.0
    ./run-tests.sh 3.14 6.0

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

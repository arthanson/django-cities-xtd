#!/bin/bash
# Test runner script for django-cities
# Usage: ./run-tests.sh [python_version] [django_version]
# Example: ./run-tests.sh 3.13 5.1
# Or: ./run-tests.sh all  (to run all test combinations)

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to run a specific test combination
run_test() {
    local python_version=$1
    local django_version=$2
    local service="test-py${python_version//./}-django${django_version//./}"

    print_info "Running tests for Python $python_version + Django $django_version"

    if docker compose up --build --exit-code-from "$service" "$service"; then
        print_success "Tests passed for Python $python_version + Django $django_version"
        return 0
    else
        print_error "Tests failed for Python $python_version + Django $django_version"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    print_info "Running all test combinations..."
    echo ""

    local failed_tests=()
    local passed_tests=()

    # Test combinations (add/remove as needed)
    # Python 3.12: Django 5.0, 5.1, 5.2, 6.0
    # Python 3.13: Django 5.1, 5.2, 6.0
    # Python 3.14: Django 5.2, 6.0
    local combinations=(
        "3.12:5.0"
        "3.12:5.1"
        "3.12:5.2"
        "3.12:6.0"
        "3.13:5.1"
        "3.13:5.2"
        "3.13:6.0"
        "3.14:5.2"
        "3.14:6.0"
    )

    for combo in "${combinations[@]}"; do
        IFS=':' read -r py_ver dj_ver <<< "$combo"
        echo ""
        print_info "========================================="
        print_info "Testing Python $py_ver with Django $dj_ver"
        print_info "========================================="

        if run_test "$py_ver" "$dj_ver"; then
            passed_tests+=("Python $py_ver + Django $dj_ver")
        else
            failed_tests+=("Python $py_ver + Django $dj_ver")
        fi
    done

    # Print summary
    echo ""
    echo "========================================="
    echo "           TEST SUMMARY"
    echo "========================================="

    if [ ${#passed_tests[@]} -gt 0 ]; then
        echo ""
        print_success "Passed (${#passed_tests[@]}):"
        for test in "${passed_tests[@]}"; do
            echo "  ✓ $test"
        done
    fi

    if [ ${#failed_tests[@]} -gt 0 ]; then
        echo ""
        print_error "Failed (${#failed_tests[@]}):"
        for test in "${failed_tests[@]}"; do
            echo "  ✗ $test"
        done
        exit 1
    else
        echo ""
        print_success "All tests passed!"
    fi
}

# Main script logic
if [ $# -eq 0 ] || [ "$1" == "all" ]; then
    run_all_tests
elif [ $# -eq 2 ]; then
    run_test "$1" "$2"
else
    echo "Usage: $0 [python_version] [django_version]"
    echo "   or: $0 all"
    echo ""
    echo "Examples:"
    echo "  $0 3.14 6.0        # Run tests for Python 3.14 + Django 6.0"
    echo "  $0 3.13 5.2        # Run tests for Python 3.13 + Django 5.2"
    echo "  $0 all             # Run all test combinations"
    echo ""
    echo "Available combinations:"
    echo "  Python 3.12: Django 5.0, 5.1, 5.2, 6.0"
    echo "  Python 3.13: Django 5.1, 5.2, 6.0"
    echo "  Python 3.14: Django 5.2, 6.0"
    exit 1
fi

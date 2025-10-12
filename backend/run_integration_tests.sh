#!/bin/bash
# Integration Test Runner
# Runs all integration tests with various options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")"

echo -e "${GREEN}CommandCenter Integration Test Runner${NC}"
echo "========================================"
echo ""

# Parse arguments
COVERAGE=false
VERBOSE=false
PARALLEL=false
QUICK=false
REPORT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --parallel|-p)
            PARALLEL=true
            shift
            ;;
        --quick|-q)
            QUICK=true
            shift
            ;;
        --report|-r)
            REPORT=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./run_integration_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage    Generate coverage report"
            echo "  -v, --verbose     Verbose output"
            echo "  -p, --parallel    Run tests in parallel"
            echo "  -q, --quick       Skip slow tests"
            echo "  -r, --report      Generate HTML coverage report"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_integration_tests.sh --coverage --verbose"
            echo "  ./run_integration_tests.sh -c -p -q"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest tests/integration/"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=term-missing"
    if [ "$REPORT" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Add quick mode (skip slow tests)
if [ "$QUICK" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'integration and not slow'"
else
    PYTEST_CMD="$PYTEST_CMD -m integration"
fi

# Add common options
PYTEST_CMD="$PYTEST_CMD --tb=short --durations=10"

echo "Running: $PYTEST_CMD"
echo ""

# Run tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✓ All integration tests passed!${NC}"

    if [ "$COVERAGE" = true ] && [ "$REPORT" = true ]; then
        echo ""
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
    fi

    exit 0
else
    echo ""
    echo -e "${RED}✗ Some integration tests failed${NC}"
    exit 1
fi

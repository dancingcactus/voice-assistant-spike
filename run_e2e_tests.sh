#!/bin/bash
# Run End-to-End Tests for Phase 1
#
# Usage:
#   ./run_e2e_tests.sh              # Run all E2E tests
#   ./run_e2e_tests.sh --fast       # Skip slow tests
#   ./run_e2e_tests.sh --perf       # Run only performance tests
#   ./run_e2e_tests.sh --char       # Run only character tests

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if server is running
echo -e "${YELLOW}Checking if server is running...${NC}"
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}Error: Server is not running at http://localhost:8000${NC}"
    echo "Please start the server first:"
    echo "  cd backend && source venv/bin/activate && uvicorn src.main:app --reload"
    exit 1
fi

echo -e "${GREEN}✓ Server is running${NC}\n"

# Change to backend directory
cd "$(dirname "$0")/backend"

# Activate virtual environment
source venv/bin/activate

# Parse arguments
TEST_ARGS="-v tests/"

case "$1" in
    --fast)
        echo -e "${YELLOW}Running fast tests only (skipping performance tests)...${NC}\n"
        TEST_ARGS="$TEST_ARGS -m 'not slow'"
        ;;
    --perf)
        echo -e "${YELLOW}Running performance tests only...${NC}\n"
        TEST_ARGS="../tests/test_e2e.py::TestE2EPerformance -v"
        ;;
    --char)
        echo -e "${YELLOW}Running character tests only...${NC}\n"
        TEST_ARGS="../tests/test_e2e.py::TestE2ECharacterModes -v"
        ;;
    --story)
        echo -e "${YELLOW}Running story beat tests only...${NC}\n"
        TEST_ARGS="../tests/test_e2e.py::TestE2EStoryBeats -v"
        ;;
    --tools)
        echo -e "${YELLOW}Running tool tests only...${NC}\n"
        TEST_ARGS="../tests/test_e2e.py::TestE2ETools -v"
        ;;
    --journey)
        echo -e "${YELLOW}Running user journey tests only...${NC}\n"
        TEST_ARGS="../tests/test_e2e.py::TestE2EUserJourney -v"
        ;;
    *)
        echo -e "${YELLOW}Running all E2E tests...${NC}\n"
        TEST_ARGS="../tests/test_e2e.py -v"
        ;;
esac

# Run tests
pytest $TEST_ARGS

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
    exit 1
fi

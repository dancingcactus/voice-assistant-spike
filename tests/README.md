# Tests Directory

This directory contains all test-related files for the Aperture Assist voice assistant system.

## Structure

```
tests/
├── scripts/           # Test scripts for milestone validation
├── __pycache__/       # Python bytecode cache (ignored)
├── conftest.py        # Pytest configuration and fixtures
└── test_e2e.py        # End-to-end integration tests
```

## Test Scripts

The `scripts/` directory contains automated test scripts for validating Phase 1.5 milestones:

- **run_e2e_tests.sh** - Full end-to-end test suite
- **test_chat_and_observability.sh** - Chat interface and observability dashboard integration
- **test_milestone2_browser.sh** - Story Beat Tool browser testing
- **test_milestone3_memory.sh** - Memory system validation
- **test_milestone4_users.sh** - User testing tool validation
- **test_milestone5_tool_calls.sh** - Tool calls inspection system
- **test_milestone6_memory_extraction.sh** - Memory extraction and retrieval
- **test_milestone7_character_tool.sh** - Character debugging tool
- **test_milestone7_polish.sh** - Final polish and integration

## Running Tests

### Backend API Tests

```bash
# Run from project root
./tests/scripts/test_milestone5_tool_calls.sh
```

### End-to-End Tests

```bash
# Run from project root
./tests/scripts/run_e2e_tests.sh
```

### Python Unit Tests

```bash
# Run from project root
pytest tests/
```

## Prerequisites

All test scripts require:

- Backend server running on `http://localhost:8000`
- Valid authorization token (default: `dev_token_12345`)
- Test data generated (see individual milestone docs)

## Documentation

For detailed testing guides, see:

- [docs/technical/phase1.5/](../docs/technical/phase1.5/) - Milestone-specific testing guides
- [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) - Common issues and solutions

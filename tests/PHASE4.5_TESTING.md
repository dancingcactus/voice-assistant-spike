# Phase 4.5 Testing Guide

## Milestone 1: Intent Detection System

### Prerequisites

1. Backend server must be running:
   ```bash
   cd backend
   source venv/bin/activate
   python -m uvicorn src.main:app --port 8000 --reload
   ```

2. Environment variables configured in `backend/.env`

### Running Tests

#### Run all Milestone 1 tests:
```bash
pytest tests/test_phase4_5_milestone1.py -v
```

#### Run specific test suites:
```bash
# Intent detection tests
pytest tests/test_phase4_5_milestone1.py::TestIntentDetection -v

# Accuracy tests
pytest tests/test_phase4_5_milestone1.py::TestIntentAccuracy -v
```

#### Run a single test:
```bash
pytest tests/test_phase4_5_milestone1.py::TestIntentDetection::test_cooking_intent_timer -v
```

### Manual Testing with curl

#### Test cooking intent:
```bash
curl -X POST http://localhost:8000/api/debug/detect-intent \
  -H "Content-Type: application/json" \
  -d '{"query": "Set a timer for 30 minutes"}' | python -m json.tool
```

#### Test household intent:
```bash
curl -X POST http://localhost:8000/api/debug/detect-intent \
  -H "Content-Type: application/json" \
  -d '{"query": "Add milk to shopping list"}' | python -m json.tool
```

#### Test multi-task intent:
```bash
curl -X POST http://localhost:8000/api/debug/detect-intent \
  -H "Content-Type: application/json" \
  -d '{"query": "Set a timer for 20 minutes and add eggs to the list"}' | python -m json.tool
```

#### Get intent detector statistics:
```bash
curl -X GET http://localhost:8000/api/debug/intent-stats | python -m json.tool
```

### Test Results (February 12, 2026)

- **TestIntentDetection**: 15/15 tests passing ✅
- **TestIntentAccuracy**: 16/16 tests passing ✅
- **Overall accuracy**: 100% on test dataset
- **Performance**: 
  - Rule-based classification: <1ms
  - LLM classification: ~4-5 seconds

### Test Dataset

The test dataset is located at `tests/test_dataset_intent_detection.json` and contains:
- 100 sample queries with expected intents
- Covers all intent categories: cooking, household, smart_home, general, multi_task
- Includes confidence thresholds for each query

### Debug API Endpoints

All debug endpoints are available at `/api/debug/*`:

- `POST /api/debug/detect-intent` - Classify a query without executing it
- `GET /api/debug/intent-stats` - Get intent detection system statistics

Full API documentation available at: http://localhost:8000/docs

### Next Steps

Once Milestone 1 is validated, proceed to Milestone 2: Character Planning System

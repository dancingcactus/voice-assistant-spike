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

---

## Milestone 2: Character Planning System

### Prerequisites

1. Backend server must be running:
   ```bash
   cd backend
   source venv/bin/activate
   python -m uvicorn src.main:app --port 8000 --reload
   ```

2. Environment variables configured in `backend/.env`

3. Milestone 1 (Intent Detection) must be complete and passing

### Running Tests

#### Run all Milestone 2 tests:
```bash
pytest tests/test_phase4_5_milestone2.py -v
```

#### Run specific test suites:
```bash
# Character planning tests
pytest tests/test_phase4_5_milestone2.py::TestCharacterPlanning -v

# Multi-task planning tests
pytest tests/test_phase4_5_milestone2.py::TestMultiTaskPlanning -v

# Handoff logic tests
pytest tests/test_phase4_5_milestone2.py::TestHandoffLogic -v

# Character assignment tests
pytest tests/test_phase4_5_milestone2.py::TestCharacterAssignments -v
```

#### Run a single test:
```bash
pytest tests/test_phase4_5_milestone2.py::TestCharacterPlanning::test_cooking_intent_delilah -v
```

### Manual Testing with curl

#### Test cooking intent plan (should assign to Delilah):
```bash
curl -X POST http://localhost:8000/api/debug/create-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Set a timer for 30 minutes"}' | python -m json.tool
```

Expected output:
```json
{
  "query": "Set a timer for 30 minutes",
  "intent_result": {
    "intent": "cooking",
    "confidence": 0.95,
    "classification_method": "rule_based"
  },
  "character_plan": {
    "tasks": [
      {
        "character": "delilah",
        "task_description": "Handle cooking query",
        "intent": "cooking",
        "confidence": 0.95,
        "requires_handoff": false,
        "handoff_from": null,
        "estimated_duration_ms": 2000
      }
    ],
    "execution_mode": "single",
    "total_confidence": 0.95,
    "estimated_total_duration_ms": 2000
  }
}
```

#### Test household intent plan:
```bash
curl -X POST http://localhost:8000/api/debug/create-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Add milk to shopping list"}' | python -m json.tool
```

#### Test multi-task query:
```bash
curl -X POST http://localhost:8000/api/debug/create-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Set a timer for 20 minutes and add eggs to the list"}' | python -m json.tool
```

Expected output should show:
- Multiple tasks in the plan
- Sequential execution mode (if different characters)
- Handoff flags set appropriately
- Total duration = sum of task durations + handoff overhead

#### Test smart home intent:
```bash
curl -X POST http://localhost:8000/api/debug/create-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Turn on the kitchen lights"}' | python -m json.tool
```

### Test Coverage

The Milestone 2 test suite covers:

1. **Character Planning** (5 tests)
   - Cooking intents → Delilah
   - Household intents → Delilah (Chapter 1) / Hank (Chapter 2+)
   - Smart home intents
   - General intents
   - Default character fallback

2. **Multi-Task Planning** (4 tests)
   - Multi-task detection
   - Sequential execution mode
   - Confidence score averaging
   - Time estimation for multiple tasks

3. **Handoff Logic** (2 tests)
   - No handoffs in single-character plans
   - Handoff metadata in multi-character plans

4. **Plan Metadata** (4 tests)
   - Processing time metrics
   - Chapter information
   - Available characters list
   - Classification method tracking

5. **Character Assignments** (2 tests)
   - Cooking tasks always → Delilah
   - Low-confidence fallback to default

6. **Execution Time Estimates** (2 tests)
   - Single task duration
   - Multi-task duration calculation

7. **Error Handling** (2 tests)
   - Empty query rejection
   - Invalid query fallback

**Total: 21 test cases**

### Key Validation Points

#### Single-Character Plans
- ✅ Cooking queries assigned to Delilah
- ✅ Execution mode = "single"
- ✅ No handoff flags set
- ✅ Confidence matches intent confidence
- ✅ Reasonable time estimates (< 5000ms for simple tasks)

#### Multi-Task Plans
- ✅ Multiple tasks detected and decomposed
- ✅ Each task has character assignment
- ✅ Execution mode = "sequential" (or "single" if same character)
- ✅ Handoff flags set when character changes
- ✅ Total time = sum of tasks + handoff overhead
- ✅ Averaged confidence across tasks

#### Chapter-Based Assignment
- ✅ Chapter 1: Delilah handles everything
- ✅ Chapter 2+: Hank handles household/smart_home
- ✅ Available characters list matches chapter

### Debug API Endpoints

All debug endpoints are available at `/api/debug/*`:

- `POST /api/debug/detect-intent` - Classify query intent (Milestone 1)
- `POST /api/debug/create-plan` - Create character plan (Milestone 2)
- `GET /api/debug/intent-stats` - Get intent detection statistics

Full API documentation available at: http://localhost:8000/docs

### Performance Benchmarks

**Target Performance:**
- Character planning: < 100ms
- Total pipeline (intent + plan): < 5 seconds (with LLM)
- Total pipeline (intent + plan): < 50ms (rule-based)

**Actual Performance** (to be measured):
- Character planning: _[TBD]_ms
- Intent detection (rule-based): _[TBD]_ms
- Intent detection (LLM): _[TBD]_ms
- Total pipeline: _[TBD]_ms

### Common Issues

#### Issue: Plan shows Delilah for household tasks in Chapter 2+
**Solution:** Make sure the user_id in the request allows chapter progression. Default `debug_user` may be stuck in Chapter 1.

#### Issue: Multi-task queries not detected
**Solution:** Check that the query has clear multi-task indicators (connector words like "and", "then", etc.). Review `config/intent_patterns.json` for multi-task patterns.

#### Issue: Handoff flags not set correctly
**Solution:** Verify that tasks have different characters assigned. In Chapter 1, all tasks go to Delilah, so no handoffs are needed.

### Next Steps

Once Milestone 2 is validated, proceed to Milestone 3: Tool Execution Integration

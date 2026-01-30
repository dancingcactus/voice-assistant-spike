# Phase X: [Phase Name] - Testing Guide

**Version:** 1.0
**Last Updated:** YYYY-MM-DD
**Status:** Draft | In Progress | Complete

---

## Overview

This guide provides step-by-step manual testing procedures for Phase X. Use this to validate functionality after E2E tests pass and before marking milestones complete.

**Purpose:**

- Validate user-facing functionality works as expected
- Catch edge cases that automated tests might miss
- Ensure UX meets quality standards
- Document expected vs actual behavior

**Who Uses This:**

- Developers completing milestones
- AI assistants validating implementations
- QA testers (if applicable)
- Future developers understanding feature behavior

---

## Prerequisites

### Required Services

Before starting any tests, ensure these services are running:

**Backend API:**

```bash
cd backend
source venv/bin/activate
python -m uvicorn src.observability.api:app --reload --port 8000
```

- Should see: "Application startup complete"
- Health check: `curl http://localhost:8000/api/v1/health`
- Expected: `{"status": "ok"}`

**Frontend:**

```bash
cd frontend
npm run dev
```

- Should see: "Local: <http://localhost:5173>"
- Open in browser: No console errors

**[Additional Service]:** (if applicable)

```bash
[command to start]
```

---

### Test Data

**Required Data:**

**Setup Commands:**

```bash
# Create test data (if needed)
cd backend
python scripts/create_test_data.py

# Or copy sample data
cp data/samples/test_user.json data/users/
```

**Verify Data:**

```bash
# Check data exists
ls -la data/users/
# Should see: test_user.json, user_justin.json
```

---

### Environment Configuration

**Environment Variables:**

```bash
# Backend .env
ENV=development
API_BASE_URL=http://localhost:8000
LOG_LEVEL=DEBUG

# Frontend .env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Browser:**

- Chrome or Firefox (latest version)
- No ad blockers that might interfere
- JavaScript enabled
- Clear cache if testing UI changes

---

## Milestone 1: [Milestone Name]

### Test 1: [Feature Name - Happy Path]

**Objective:** Verify [specific user capability]

**Prerequisites:**

- [Any specific setup needed]
- [Data or state required]

**Steps:**

1. **[Action 1]**

   ```
   [Detailed instruction - e.g., "Navigate to http://localhost:5173/dashboard"]
   ```

   - **Expected:** [What you should see - e.g., "Dashboard loads, shows header with user name"]
   - **Actual:** [Fill in during testing]
   - **Screenshot:** [Optional - where to save]

2. **[Action 2]**

   ```
   [Detailed instruction - e.g., "Click 'Create Agent' button"]
   ```

   - **Expected:** [What should happen - e.g., "Modal opens with empty form"]
   - **Actual:** [Fill in during testing]

3. **[Action 3]**

   ```
   [Detailed instruction]
   ```

   - **Expected:** [Expected outcome]
   - **Actual:** [Fill in during testing]

4. **[Action 4]**

   ```
   [Detailed instruction]
   ```

   - **Expected:** [Expected outcome]
   - **Actual:** [Fill in during testing]

**Final Verification:**

- ✅ [Check 1 - e.g., "Agent appears in list"]
- ✅ [Check 2 - e.g., "Success message displayed"]
- ✅ [Check 3 - e.g., "No console errors"]
- ✅ [Check 4 - e.g., "Backend logs show successful creation"]

**Backend Verification:**

```bash
# Check backend logs
tail -f backend/logs/app.log | grep agent_create

# Check data file
cat data/agents/agent_[id].json
# Should show newly created agent
```

**Status:** ⏳ Not Tested | ✅ Pass | ❌ Fail

**Notes:** [Any observations, issues, or deviations]

---

### Test 2: [Feature Name - Error Handling]

**Objective:** Verify system handles errors gracefully

**Prerequisites:**

- [Setup that will cause error]

**Steps:**

1. **[Action that triggers error]**

   ```
   [Detailed instruction]
   ```

   - **Expected:** [Error message or behavior]
   - **Actual:** [Fill in during testing]

2. **[Verify error recovery]**

   ```
   [Instruction to fix error condition]
   ```

   - **Expected:** [System recovers, allows retry]
   - **Actual:** [Fill in during testing]

**Error Verification:**

- ✅ Error message is user-friendly
- ✅ Error message explains what went wrong
- ✅ Error message suggests how to fix it
- ✅ System state remains consistent (no partial updates)
- ✅ Can recover without page reload

**Status:** ⏳ Not Tested | ✅ Pass | ❌ Fail

**Notes:** [Observations]

---

### Test 3: [Feature Name - Edge Case]

**Objective:** Test boundary conditions or unusual inputs

**Prerequisites:**

- [Special setup for edge case]

**Edge Case Scenarios:**

**Scenario A: [Description - e.g., "Empty input"]**

1. [Action with empty/null/zero input]
   - **Expected:** [Validation error or default behavior]
   - **Actual:** [Fill in during testing]

**Scenario B: [Description - e.g., "Maximum values"]**

1. [Action with very large input]
   - **Expected:** [Handles gracefully or shows limit]
   - **Actual:** [Fill in during testing]

**Scenario C: [Description - e.g., "Concurrent access"]**

1. [Action in multiple tabs simultaneously]
   - **Expected:** [Proper concurrency handling]
   - **Actual:** [Fill in during testing]

**Status:** ⏳ Not Tested | ✅ Pass | ❌ Fail

**Notes:** [Observations]

---

### Test 4: [Integration Test - Multiple Features]

**Objective:** Verify features work together correctly

**Prerequisites:**

- [Both features set up]

**Steps:**

1. **[Use Feature A]**
   - **Expected:** [Result from Feature A]
   - **Actual:** [Fill in during testing]

2. **[Use Feature B with Feature A's output]**
   - **Expected:** [Feature B sees Feature A's changes]
   - **Actual:** [Fill in during testing]

3. **[Verify end-to-end flow]**
   - **Expected:** [Complete workflow successful]
   - **Actual:** [Fill in during testing]

**Status:** ⏳ Not Tested | ✅ Pass | ❌ Fail

**Notes:** [Observations]

---

## Milestone 2: [Milestone Name]

[Same structure as Milestone 1]

### Test 1: [Feature Name]

[Full test structure]

### Test 2: [Feature Name]

[Full test structure]

---

## Milestone 3: [Milestone Name]

[Same structure as Milestone 1]

---

## Cross-Milestone Integration Tests

### Integration Test 1: [Scenario Spanning Multiple Milestones]

**Objective:** Verify milestones work together

**Prerequisites:**

- All milestones 1-3 complete

**Workflow:**

1. **[Use Milestone 1 feature]**
2. **[Use Milestone 2 feature on Milestone 1's output]**
3. **[Use Milestone 3 feature on previous results]**
4. **[Verify complete end-to-end flow]**

**Expected Flow:**

```
User action → Milestone 1 → Milestone 2 → Milestone 3 → Final result
```

**Final Verification:**

- ✅ All features work together seamlessly
- ✅ No data loss between features
- ✅ Performance acceptable for full workflow
- ✅ No UI glitches during transitions

**Status:** ⏳ Not Tested | ✅ Pass | ❌ Fail

---

## Regression Tests (Previous Phase Features)

### Regression Test 1: [Critical Feature from Previous Phase]

**Objective:** Ensure Phase X didn't break Phase [Y] functionality

**Steps:**

1. **[Use existing feature]**
   - **Expected:** [Same behavior as before Phase X]
   - **Actual:** [Fill in during testing]

2. **[Verify data compatibility]**
   - **Expected:** [Old data still works]
   - **Actual:** [Fill in during testing]

**Status:** ⏳ Not Tested | ✅ Pass | ❌ Fail

---

### Regression Test 2: [Another Critical Feature]

[Same structure]

---

## Performance Testing

### Performance Test 1: [Latency Measurement]

**Objective:** Verify performance targets met (from PRD)

**Target:** [Specific metric - e.g., "Agent selection < 100ms"]

**Measurement Method:**

1. **[Perform action 10 times]**
2. **[Record latency for each]**
   - Use browser DevTools Network tab or backend logs
3. **[Calculate average and p90]**

**Results:**

- Run 1: [X]ms
- Run 2: [X]ms
- Run 3: [X]ms
- Run 4: [X]ms
- Run 5: [X]ms
- Run 6: [X]ms
- Run 7: [X]ms
- Run 8: [X]ms
- Run 9: [X]ms
- Run 10: [X]ms

**Statistics:**

- Average: [X]ms
- P90: [X]ms
- Target: [X]ms
- **Status:** ✅ Met | ❌ Missed

**Notes:** [Observations about performance]

---

### Performance Test 2: [Load Testing]

**Objective:** Verify system handles expected load

**Setup:**

```bash
# Generate test load
[command to create load]
```

**Measurements:**

- Requests per second: [X]
- Average latency: [X]ms
- Error rate: [X]%

**Status:** ✅ Met | ❌ Missed

---

## Usability Testing

### Usability Test 1: [First-Time User Flow]

**Objective:** Verify new user can discover and use features

**Scenario:** User has never seen this feature before

**Steps:**

1. **[Present interface without instructions]**
2. **[Observe where user clicks first]**
   - **Expected:** [Intuitive action]
   - **Actual:** [What happened]

3. **[Watch for confusion or errors]**
   - **Issues Observed:** [List any confusion points]

4. **[Time to complete task]**
   - **Time:** [X] seconds
   - **Target:** [Y] seconds

**UX Observations:**

- ✅ Feature discoverable without documentation
- ✅ Labels and buttons self-explanatory
- ✅ Error messages helpful
- ✅ No dead ends or confusion
- ❌ [Any issues found]

**Suggested Improvements:**

- [Suggestion 1]
- [Suggestion 2]

---

## Browser Compatibility (Optional)

If features use cutting-edge browser APIs, test across browsers:

### Chrome

- Version: [X]
- Status: ✅ Works | ❌ Issues
- Notes: [Any browser-specific behavior]

### Firefox

- Version: [X]
- Status: ✅ Works | ❌ Issues
- Notes: [Any browser-specific behavior]

### Safari

- Version: [X]
- Status: ✅ Works | ❌ Issues
- Notes: [Any browser-specific behavior]

---

## Troubleshooting

### Issue: [Common Problem 1]

**Symptom:** [What user sees]

**Cause:** [Why it happens]

**Solution:**

```bash
[Commands or actions to fix]
```

**Prevention:** [How to avoid this issue]

---

### Issue: [Common Problem 2]

[Same structure]

---

### Issue: Services Won't Start

**Symptom:** Backend or frontend fails to start

**Debugging Steps:**

```bash
# Check ports in use
lsof -i :8000
lsof -i :5173

# Check logs
tail -f backend/logs/app.log
tail -f frontend/.vite/log

# Restart services
[kill and restart commands]
```

---

### Issue: E2E Tests Failing Locally

**Symptom:** Tests pass on CI but fail locally

**Common Causes:**

- Browser version mismatch
- Port conflicts
- Stale test data
- Environment variables not set

**Solutions:**

```bash
# Update Playwright browsers
npx playwright install

# Clean test data
rm -rf data/test/*

# Reset environment
cp .env.example .env
```

---

## Test Data Cleanup

**After Testing:**

1. **Remove Test Data:**

   ```bash
   cd backend
   python scripts/cleanup_test_data.py
   ```

2. **Reset Database (if applicable):**

   ```bash
   [reset command]
   ```

3. **Clear Browser Data:**
   - Open DevTools → Application → Clear storage

---

## AI Validation Instructions

**For AI Assistants:**

When validating a milestone:

1. **Read Test Section** for that milestone
2. **Execute Each Test Step** using available tools:
   - `Bash` for backend commands
   - `mcp__playwright__*` for browser automation
   - `Read` to verify data files
3. **Compare Results** to expected outcomes
4. **Document Findings:**
   - Fill in "Actual" fields
   - Mark status as Pass/Fail
   - Add notes for any deviations
5. **Report Summary:**

   ```
   Milestone X Testing Results:
   - Test 1: ✅ Pass - All steps completed successfully
   - Test 2: ✅ Pass - Error handling works as expected
   - Test 3: ❌ Fail - Edge case Z not handled (see notes)
   - Test 4: ✅ Pass - Integration successful

   Overall: 3/4 tests passing, 1 issue found (non-blocking)
   ```

---

## Test Coverage Summary

### Milestone 1

- [ ] Test 1: [Name] - Happy path
- [ ] Test 2: [Name] - Error handling
- [ ] Test 3: [Name] - Edge cases
- [ ] Test 4: [Name] - Integration

### Milestone 2

- [ ] Test 1: [Name]
- [ ] Test 2: [Name]
- [ ] Test 3: [Name]

### Milestone 3

- [ ] Test 1: [Name]
- [ ] Test 2: [Name]

### Cross-Milestone

- [ ] Integration Test 1
- [ ] Integration Test 2

### Regression

- [ ] Regression Test 1
- [ ] Regression Test 2

### Performance

- [ ] Performance Test 1
- [ ] Performance Test 2

### Usability

- [ ] Usability Test 1

**Total Tests:** [X]
**Tests Passed:** [Y]
**Tests Failed:** [Z]
**Coverage:** [Y/X * 100]%

---

## Sign-Off

### Milestone 1: [Name]

- **Tested By:** [Name or AI]
- **Date:** YYYY-MM-DD
- **Status:** ✅ Approved | ❌ Needs Fixes
- **Notes:** [Summary]

### Milestone 2: [Name]

- **Tested By:** [Name or AI]
- **Date:** YYYY-MM-DD
- **Status:** ✅ Approved | ❌ Needs Fixes
- **Notes:** [Summary]

### Milestone 3: [Name]

- **Tested By:** [Name or AI]
- **Date:** YYYY-MM-DD
- **Status:** ✅ Approved | ❌ Needs Fixes
- **Notes:** [Summary]

### Phase X Overall

- **Tested By:** [Name]
- **Date:** YYYY-MM-DD
- **Status:** ✅ Ready for Release | ❌ Needs Work
- **Notes:** [Overall assessment]

---

## Appendix

### Test Data Reference

[List any test data structures, sample inputs, or reference data]

### API Testing Commands

[Common curl commands for manual API testing]

```bash
# Example: List agents
curl -H "Authorization: Bearer dev_token_12345" \
  http://localhost:8000/api/v1/agents

# Example: Create agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer dev_token_12345" \
  -H "Content-Type: application/json" \
  -d '{"name":"TestAgent","type":"helper"}'
```

### Screenshots Location

All test screenshots should be saved to:

```
docs/technical/phaseX/screenshots/
├── milestone1_test1_step1.png
├── milestone1_test1_step2.png
└── ...
```

---

## Changelog

### Version 1.0 - YYYY-MM-DD

- Initial testing guide created
- All milestones documented

### Version 1.1 - YYYY-MM-DD (if updated during testing)

- [Changes based on testing experience]
- [New edge cases added]

---

**Document Owner:** [Name]
**Last Review:** YYYY-MM-DD
**Next Review:** After milestone completion

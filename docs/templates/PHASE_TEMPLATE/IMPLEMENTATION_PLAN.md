# Phase X: [Phase Name] - Implementation Plan

**Version:** 1.0
**Last Updated:** YYYY-MM-DD
**Status:** ⏳ Not Started | 🚧 In Progress | ✅ Complete

---

## References

- **PRD**: [PRD.md](PRD.md) - Product requirements and user stories
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - Technical design and system components
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md) - Manual test procedures

---

## Overview

### Goals

[Brief summary of what this phase delivers - pulled from PRD]

Example:
> Implement multi-agent coordination system enabling Delilah and Hank to collaborate on queries through intelligent bidding and handoffs.

### Timeline Estimate

- **Total Duration:** [X weeks]
- **Milestone Count:** [N milestones]
- **Milestone Cadence:** [X days per milestone]
- **Target Completion:** [YYYY-MM-DD]

### Success Criteria (Phase Level)

- ✅ All [N] milestones complete
- ✅ E2E Playwright tests passing for all features
- ✅ Manual testing guide complete and validated
- ✅ All phase documentation updated
- ✅ Ready for integration with next phase

---

## Milestone 1: [Milestone Name]

**Status:** ⏳ Not Started | 🚧 In Progress | ✅ Complete
**Duration:** [X days]
**Goal:** [One-sentence description of what this milestone delivers]
**Completed:** [YYYY-MM-DD] (fill in when done)

---

### What Gets Built

#### Backend Components

- **[Component 1]** - [Description]
  - File: `[path/to/component.py]`
  - Purpose: [What it does]
  - Key methods: [method1(), method2()]

- **[Component 2]** - [Description]
  - File: `[path/to/component.py]`
  - Purpose: [What it does]
  - Key methods: [method1(), method2()]

#### Frontend Components

- **[Component 1]** - [Description]
  - File: `[path/to/Component.tsx]`
  - Purpose: [What it does]
  - Props: [Key props]

- **[Component 2]** - [Description]
  - File: `[path/to/Component.tsx]`
  - Purpose: [What it does]
  - Props: [Key props]

#### API Endpoints

```
GET    /api/v1/[resource]              # [Description]
POST   /api/v1/[resource]              # [Description]
PUT    /api/v1/[resource]/{id}         # [Description]
DELETE /api/v1/[resource]/{id}         # [Description]
```

#### Data Models

```typescript
interface ModelName {
  id: string;
  field1: type;
  field2: type;
  created_at: Date;
}
```

---

### Completion Checklist

**Code:**
- [ ] All backend components implemented and tested
- [ ] All frontend components implemented and styled
- [ ] API endpoints created and documented
- [ ] Data models defined and validated
- [ ] Code compiles without errors
- [ ] No linting warnings

**Testing:**
- [ ] E2E Playwright tests written for all user-facing features
  - Location: `tests/e2e/phaseX/milestone1_[name].spec.ts`
- [ ] All E2E tests passing
- [ ] AI executed manual test steps from TESTING_GUIDE.md
- [ ] Manual test instructions documented (See TESTING_GUIDE.md § Milestone 1)
- [ ] Edge cases identified and tested
- [ ] Error handling verified

**Integration:**
- [ ] Integrates with existing Phase [X] features
- [ ] No regressions in previous functionality
- [ ] All dependencies satisfied
- [ ] Configuration properly set up

**Documentation:**
- [ ] Code includes docstrings/comments
- [ ] API endpoints documented in ARCHITECTURE.md
- [ ] Manual testing steps in TESTING_GUIDE.md
- [ ] Blockers/discoveries documented below

**Git:**
- [ ] Changes committed to phase branch
- [ ] Commit message follows format
- [ ] One commit per milestone

---

### Success Criteria

User-facing outcomes that must be achieved:

- ✅ [Criterion 1 - e.g., "User can create agent and see it in list"]
- ✅ [Criterion 2 - e.g., "Agent bidding completes in < 100ms"]
- ✅ [Criterion 3 - e.g., "Error messages are helpful and actionable"]
- ✅ [Criterion 4 - e.g., "UI updates reflect backend changes immediately"]

---

### Blockers/Discoveries

[Document any issues encountered during implementation]

**Blockers:**
- [Date]: [Description of blocker]
  - **Impact:** [How it affects milestone]
  - **Resolution:** [How it was or will be resolved]

**Discoveries:**
- [Date]: [Unexpected finding or learning]
  - **Impact:** [How it affects design or future work]
  - **Action:** [What was done about it]

**Example:**
```
Blockers:
- 2026-01-29: Agent bidding occasionally exceeds 100ms target
  - Impact: Performance requirement at risk
  - Resolution: Added caching for agent configs, now averaging 45ms

Discoveries:
- 2026-01-30: Discovered need for agent availability checking
  - Impact: Should add health checks for agents
  - Action: Added to Milestone 3 scope
```

---

### E2E Test Summary

**Test File:** `tests/e2e/phaseX/milestone1_[name].spec.ts`

**Test Coverage:**
- ✅ [Test 1 - e.g., "Agent registration flow"]
- ✅ [Test 2 - e.g., "Agent listing with filters"]
- ✅ [Test 3 - e.g., "Agent deletion with confirmation"]

**Results:**
- [X] tests passing
- [0] tests failing
- [Status: All Green / Needs Fix]

(See TESTING_GUIDE.md for manual test procedures)

---

### Files Created/Modified

**Created:**
- `[path/to/new/file.py]` ([X] lines) - [Purpose]
- `[path/to/new/Component.tsx]` ([X] lines) - [Purpose]
- `tests/e2e/phaseX/milestone1_test.spec.ts` ([X] lines) - [Purpose]

**Modified:**
- `[path/to/existing/file.py]` (+[X] lines) - [Changes made]
- `[path/to/existing/Component.tsx]` (+[X] lines) - [Changes made]

**Dependencies Added:**
- `[package-name]` ([version]) - [Why needed]

---

## Milestone 2: [Milestone Name]

**Status:** ⏳ Not Started | 🚧 In Progress | ✅ Complete
**Duration:** [X days]
**Goal:** [One-sentence description]
**Completed:** [YYYY-MM-DD] (fill in when done)

[Same structure as Milestone 1]

---

## Milestone 3: [Milestone Name]

**Status:** ⏳ Not Started | 🚧 In Progress | ✅ Complete
**Duration:** [X days]
**Goal:** [One-sentence description]
**Completed:** [YYYY-MM-DD] (fill in when done)

[Same structure as Milestone 1]

---

## Testing Strategy

### E2E Test Organization

**Location:** `tests/e2e/phaseX/`

**Test Files:**
```
tests/e2e/phaseX/
├── milestone1_[name].spec.ts          # Tests for Milestone 1
├── milestone2_[name].spec.ts          # Tests for Milestone 2
├── milestone3_[name].spec.ts          # Tests for Milestone 3
└── README.md                          # Phase test documentation
```

**Running Tests:**
```bash
# Run all phase X tests
npx playwright test tests/e2e/phaseX

# Run specific milestone tests
npx playwright test tests/e2e/phaseX/milestone1_*.spec.ts

# Run with UI
npx playwright test --ui
```

**Test Requirements:**
- Every user-facing feature must have E2E test coverage
- Tests must verify both UI and backend integration
- Tests must include error scenarios
- Tests must be deterministic (no flaky tests)

---

### Manual Testing

**Documentation:** See [TESTING_GUIDE.md](TESTING_GUIDE.md)

**Process:**
1. Complete automated E2E tests first
2. Follow manual test procedures in TESTING_GUIDE.md
3. AI validates by executing manual tests
4. Document results in milestone completion checklist
5. Flag any issues or discrepancies

**AI Validation:**
- AI reads TESTING_GUIDE.md instructions
- AI executes each manual test step
- AI compares actual vs expected results
- AI documents findings in Blockers/Discoveries section
- AI marks checklist items as complete or flags issues

---

### Integration Testing

**Cross-Feature Tests:**
- [ ] Milestone 1 + Milestone 2 integration
- [ ] Milestone 2 + Milestone 3 integration
- [ ] All milestones working together

**Regression Tests:**
- [ ] Previous phase features still working
- [ ] No performance degradation
- [ ] No UI/UX regressions

---

## Phase Completion Criteria

### All Milestones Complete

- ✅ Milestone 1: [Name] - ⏳ Status
- ✅ Milestone 2: [Name] - ⏳ Status
- ✅ Milestone 3: [Name] - ⏳ Status

### Testing Complete

- ✅ All E2E tests passing ([X]/[N] test files green)
- ✅ All manual tests validated by AI
- ✅ Integration tests passing
- ✅ Regression tests passing
- ✅ No known critical bugs

### Documentation Complete

- ✅ All API endpoints documented in ARCHITECTURE.md
- ✅ All manual tests documented in TESTING_GUIDE.md
- ✅ User-facing docs updated (if applicable)
- ✅ TROUBLESHOOTING.md updated with new solutions
- ✅ Completion report written (optional)

### Code Quality

- ✅ No TypeScript compilation errors
- ✅ No Python linting errors
- ✅ All code reviewed and approved
- ✅ Performance targets met (see PRD metrics)

### Ready for Next Phase

- ✅ Phase branch merged to main (or ready to merge)
- ✅ Git tag created: `phaseX-complete`
- ✅ Dependencies for next phase satisfied
- ✅ Handoff documentation prepared

---

## Risk Management

### Known Risks

**Risk 1:** [Description from ARCHITECTURE.md]
- **Mitigation:** [Strategy]
- **Status:** [Active monitoring | Mitigated | Occurred]
- **Owner:** [Who tracks this]

**Risk 2:** [Description]
- [Same structure]

### Issues Encountered

[Track issues found during implementation]

**Issue 1:** [Date] - [Description]
- **Severity:** Critical | High | Medium | Low
- **Impact:** [What it affects]
- **Status:** Open | In Progress | Resolved
- **Resolution:** [How it was fixed]

---

## Timeline Tracking

### Planned vs Actual

| Milestone | Planned Days | Actual Days | Variance | Notes |
|-----------|--------------|-------------|----------|-------|
| Milestone 1 | [X] | [Y] | [+/-Z] | [Reason for variance] |
| Milestone 2 | [X] | [Y] | [+/-Z] | [Reason for variance] |
| Milestone 3 | [X] | [Y] | [+/-Z] | [Reason for variance] |
| **Total** | **[X]** | **[Y]** | **[+/-Z]** | |

### Weekly Progress Updates

**Week 1 (YYYY-MM-DD to YYYY-MM-DD):**
- Completed: [List accomplishments]
- In Progress: [Current work]
- Blockers: [Any issues]
- Next Week: [Planned work]

**Week 2 (YYYY-MM-DD to YYYY-MM-DD):**
- [Same structure]

---

## Dependencies

### Prerequisites (Must Complete Before Starting)

- ✅ Phase [X] complete
- ✅ [Specific feature] available
- ✅ [Configuration] set up
- ✅ [Data migration] complete (if applicable)

### Enables (Unblocks After Completion)

- Phase [Y]: [Specific dependency this phase satisfies]
- Phase [Z]: [Specific dependency this phase satisfies]

---

## Future Enhancements

**Deferred to Later Phases:**

Items discovered during implementation that are valuable but out of scope:

1. **[Enhancement Name]**
   - **Description:** [What this would add]
   - **Value:** [Why it's valuable]
   - **Effort:** [Estimated effort]
   - **Recommended For:** Phase [X] or Release [Y]

2. **[Enhancement Name]**
   - [Same structure]

---

## Lessons Learned

[Document insights gained during implementation - fill in as phase progresses]

### What Went Well

- [Success 1]: [Description and why it worked]
- [Success 2]: [Description and why it worked]

### What Could Be Improved

- [Challenge 1]: [Description and how to improve next time]
- [Challenge 2]: [Description and how to improve next time]

### Technical Insights

- [Insight 1]: [Learning about architecture, tools, or approach]
- [Insight 2]: [Learning about architecture, tools, or approach]

### Process Improvements

- [Improvement 1]: [Suggestion for future phases]
- [Improvement 2]: [Suggestion for future phases]

---

## Quick Reference

### Git Workflow for This Phase

```bash
# Start phase (if not already created)
git checkout -b phaseX

# After completing a milestone
git add .
git commit -m "Complete Milestone X: [Name] for Phase Y

[Brief description]

Changes:
- [Change 1]
- [Change 2]

Testing:
- E2E tests in tests/e2e/phaseX/milestoneX_*.spec.ts

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# After completing all milestones
git tag phaseX-complete
git push --tags

# Merge to main (when ready)
git checkout main
git merge phaseX --no-ff
git push
```

### Running Tests

```bash
# Backend tests (if any)
cd backend
pytest

# E2E tests
npx playwright test tests/e2e/phaseX

# Specific milestone tests
npx playwright test tests/e2e/phaseX/milestone1_*.spec.ts

# With UI for debugging
npx playwright test --ui
```

### Starting Services

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python -m uvicorn src.observability.api:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## Appendix

### Code Style Guide

**Python:**
- Follow PEP 8
- Use type hints
- Docstrings for all public functions
- Maximum line length: 100 characters

**TypeScript:**
- Use ESLint configuration
- Prefer interfaces over types
- Use functional components
- Props destructuring

### Commit Message Format

```
Complete Milestone X: [Short Description] for Phase Y

[Detailed description of what was built and why]

Changes:
- [Bullet point list of major changes]
- [Focus on user-facing or architectural changes]

Testing:
- [How this was tested]
- [Location of E2E tests]

[Optional: Technical notes or breaking changes]

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Changelog

### Version 1.0 - YYYY-MM-DD
- Initial implementation plan created
- Milestones defined
- Timeline estimated

### Version 1.1 - YYYY-MM-DD (if applicable during development)
- [Milestone X completed]
- [Updated estimates based on progress]
- [Added new risk or blocker]

---

**Plan Owner:** [Name]
**Last Review:** YYYY-MM-DD
**Next Review:** [After each milestone completion]

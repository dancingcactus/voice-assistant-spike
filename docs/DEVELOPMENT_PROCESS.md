# Development Process

**Version:** 1.0
**Last Updated:** 2026-01-29
**Status:** Active

---

## Introduction

This document defines the development methodology for the Aperture Assist voice assistant project. It establishes a structured approach to planning, implementing, and releasing features across multiple development cycles.

### Who Should Read This

- **Developers** working on new features
- **AI Assistants** helping with implementation
- **Project maintainers** managing releases

### Purpose

This methodology ensures:

- Consistent documentation across all phases
- Testable increments at every level
- Clear completion criteria
- Traceable progress from concept to release

---

## Three-Layer Development Structure

Development is organized into three hierarchical layers, each with specific completion criteria and artifacts.

### Layer 1: Releases

**Definition:** Customer-facing feature deliveries that combine multiple phases into a cohesive version.

**Version Numbering:**

- **Major releases** (x.0): Significant new capabilities (e.g., v2.0 - Multi-character panel)
- **Minor releases** (x.x): Feature additions within current capabilities (e.g., v1.5 - Observability tools)

**Examples:**

- v1.0: Core single-character system with Delilah
- v1.5: Developer observability and testing infrastructure
- v2.0: Multi-character panel with Hank and Rex

**Completion Criteria:**

- ✅ All phases in release are complete
- ✅ All automated tests passing
- ✅ Manual testing performed and documented
- ✅ Release notes written
- ✅ Git tag created (e.g., `v1.5.0`)
- ✅ Phase folders moved to `docs/releases/vX.X/`
- ✅ CHANGELOG.md updated

### Layer 2: Phases

**Definition:** Testable feature sets that deliver user-facing value. Each phase represents a cohesive set of functionality that can be demonstrated and validated.

**Phase Numbering:**

- **Integer phases** (1, 2, 3): Major feature areas
- **Decimal phases** (1.5, 2.5): Intermediate features or supporting infrastructure

**Phase Relationships:**

- **Sibling phases** (Phase 2, Phase 3): Independent peer features
  - Folder structure: `docs/technical/phase2/`, `docs/technical/phase3/`
- **Sub-phases** (Phase 2, Phase 2.5): Dependent or supporting features
  - Folder structure: `docs/technical/phase2/`, `docs/technical/phase2/phase2.5/`

**Examples:**

- Phase 1: Core conversation system with Delilah
- Phase 1.5: Observability and testing tools
- Phase 2: Multi-character coordination
- Phase 2.5: Advanced character relationship tracking (sub-phase of 2)

**Completion Criteria:**

- ✅ All milestones in phase complete
- ✅ End-to-end tests written and passing
- ✅ Manual testing guide complete
- ✅ All features testable by user
- ✅ Git tag created (e.g., `phase2-complete`)
- ✅ Phase branch merged to main (optional, can wait for release)

### Layer 3: Milestones

**Definition:** Single, testable chunks of work that can be completed and verified independently. Each milestone adds one demonstrable capability to the system.

**Examples:**

- Milestone 4: User Testing Tool (from Phase 1.5)
- Milestone 5: Tool Calls Inspection (from Phase 1.5)
- Milestone 6: Memory Extraction System (from Phase 1.5)

**Completion Criteria:**

- ✅ Code complete and working
- ✅ E2E Playwright tests written and passing
- ✅ AI validation executed (AI runs manual test steps)
- ✅ Manual test instructions documented in TESTING_GUIDE.md
- ✅ Edge cases identified and documented
- ✅ Integration with existing features verified
- ✅ One git commit on phase branch

**Milestone Size Guideline:**

- Target: 1-3 days of work maximum
- If growing beyond this, break into sub-milestones
- Each milestone should have a single, clear acceptance test

---

## Git Workflow

### Branch Strategy

**Phase Branches:**

- Create when starting a new phase: `git checkout -b phase2`
- One branch per phase (e.g., `phase1.5`, `phase2`, `phase2.5`)
- Long-lived until phase complete

**Milestone Commits:**

- One commit per completed milestone
- Commit message format:

  ```
  Complete Milestone X: [Milestone Name] for Phase Y

  [Brief description of what was built]

  Changes:
  - [Key change 1]
  - [Key change 2]

  Testing:
  - [Test approach]

  🤖 Generated with Claude Code

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

**Example:**

```bash
# Start Phase 2
git checkout -b phase2

# After completing Milestone 1
git add .
git commit -m "Complete Milestone 1: Agent Bidding System for Phase 2

Implemented multi-agent bidding system for query routing

Changes:
- Agent bidding interface
- Confidence scoring
- Routing logic

Testing:
- E2E tests in tests/e2e/phase2/milestone1_bidding.spec.ts

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# After completing all milestones
git tag phase2-complete
```

### Tagging Strategy

**Phase Tags:**

- Format: `phase[number]-complete`
- Created when all milestones in phase are done
- Examples: `phase1.5-complete`, `phase2-complete`

**Release Tags:**

- Format: `v[major].[minor].[patch]`
- Created when creating an official release
- Examples: `v1.0.0`, `v1.5.0`, `v2.0.0`

**Tagging Commands:**

```bash
# Tag completed phase
git tag phase2-complete

# Tag release
git tag v2.0.0

# Push tags to remote
git push --tags
```

### Merging Strategy

**Phase to Main:**

- Merge phase branch to `main` or a release branch when phase complete
- Can defer merge until release creation
- Use merge commit (not rebase) to preserve history

```bash
# When phase is complete
git checkout main
git merge phase2 --no-ff -m "Merge phase2: Multi-character coordination"
git push
```

---

## Testing Strategy

### Primary Focus: End-to-End Testing

This project prioritizes E2E tests over unit tests during early development to ensure user-facing functionality works correctly.

**Rationale:**

- Early lifecycle project with changing architecture
- User experience is primary success metric
- E2E tests provide most confidence in feature completeness
- Unit tests will be added as code stabilizes

### E2E Test Requirements (Per Milestone)

**Location:** `tests/e2e/`

**Organization:**

```
tests/e2e/
├── phase1.5/
│   ├── milestone4_users.spec.ts
│   ├── milestone5_tool_calls.spec.ts
│   └── milestone6_memory.spec.ts
├── phase2/
│   ├── milestone1_bidding.spec.ts
│   └── milestone2_handoff.spec.ts
└── README.md
```

**Test Framework:** Playwright

**Coverage Requirements:**

- Every user-facing feature must have E2E test coverage
- Critical paths must be tested end-to-end
- Tests must verify both UI and backend integration

**Example E2E Test Structure:**

```typescript
// tests/e2e/phase2/milestone1_bidding.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Milestone 1: Agent Bidding System', () => {
  test('should route simple query to single agent', async ({ page }) => {
    // Setup
    await page.goto('http://localhost:3000');

    // Execute
    await page.fill('[data-testid="message-input"]', 'Set timer for 5 minutes');
    await page.click('[data-testid="send-button"]');

    // Verify
    await expect(page.locator('[data-testid="response"]'))
      .toContainText('Timer set for 5 minutes');
    await expect(page.locator('[data-testid="agent-used"]'))
      .toContainText('Delilah');
  });
});
```

### AI Validation Definition

**What "AI Tested" Means:**

When a milestone completion checklist says "AI executed manual test steps", it means:

1. **Execution:** The AI assistant runs the manual test procedures documented in TESTING_GUIDE.md
2. **Reporting:** The AI documents actual results vs. expected results
3. **Verification:** The AI confirms tests pass or reports failures with details
4. **Edge Cases:** The AI identifies and documents any unexpected behavior

**AI Testing Process:**

```markdown
1. AI reads TESTING_GUIDE.md for milestone
2. AI executes each test step using available tools (Playwright, Bash, etc.)
3. AI captures results (screenshots, console output, API responses)
4. AI compares actual vs. expected outcomes
5. AI documents results in completion report
6. AI flags any discrepancies or issues found
```

**Example AI Test Report:**

```markdown
### Milestone 4: User Testing Tool - AI Validation Results

**Test 1: Create Test User** ✅ PASS
- Executed: Created test user via UI
- Expected: User appears in list with "TEST" badge
- Actual: User created successfully, badge displays correctly
- Screenshot: milestone4_user_created.png

**Test 2: Delete Production User** ✅ PASS
- Executed: Attempted to delete user_justin
- Expected: Error message "Cannot delete production users"
- Actual: Correct error displayed, user not deleted
- Console: No errors logged

**Test 3: Switch Active User** ✅ PASS
- Executed: Switched from justin to test user
- Expected: All tools update to show test user context
- Actual: Memory tool shows 0 memories, Story tool shows Chapter 1
- Verification: Context switch successful across all tools
```

### Manual Testing

**Documentation Location:** Each phase's `TESTING_GUIDE.md`

**Required Elements:**

- Prerequisites (services, data, configuration)
- Step-by-step test procedures
- Expected results for each step
- Troubleshooting common issues

**Example Manual Test:**

```markdown
### Test 2: Memory Extraction

**Objective:** Verify AI automatically saves dietary restrictions

**Steps:**
1. Open chat interface (http://localhost:3000)
2. Send message: "I have Celiac disease"
3. Wait for response
4. Open observability dashboard
5. Navigate to Memories tab
6. Filter by category: "dietary_restriction"

**Expected Result:**
- New memory created with content "Has Celiac disease (gluten intolerance)"
- Importance: 9-10
- Category: dietary_restriction
- Source: "conversation_extraction"

**Troubleshooting:**
- If memory not created, check backend logs for tool call
- Verify save_memory tool is registered
- Check character instructions include memory examples
```

---

## Documentation Process

### Phase Setup Process

Follow this sequence when starting a new phase:

1. **Create PRD (Product Requirements Document)**
   - Define value proposition and user experience
   - List functional and non-functional requirements
   - Establish success metrics
   - Identify what's explicitly out of scope
   - Document open questions

2. **Create Architecture Document**
   - Design technical approach based on PRD
   - Define system components and data flows
   - Specify APIs and interfaces
   - Identify technology stack additions
   - Document integration points

3. **Create Implementation Plan**
   - Break phase into milestones (from PRD + Architecture)
   - Define completion criteria for each milestone
   - Estimate timeline and effort
   - Link to PRD and Architecture docs
   - Create milestone tracking with checklists

4. **Create Testing Guide**
   - Write manual test procedures for each milestone
   - Document prerequisites and setup
   - Define expected outcomes
   - Include troubleshooting steps

5. **Implement Milestones**
   - Follow implementation plan
   - Update status as milestones progress
   - Document blockers and discoveries
   - Commit after each milestone completion

6. **Update Documentation**
   - After phase completes, update user-facing docs
   - Add to USER_GUIDE.md if needed
   - Update TROUBLESHOOTING.md with new issues
   - Ensure all templates filled out

### Phase Folder Structure

```
docs/technical/phaseN/
├── PRD.md                          # Product requirements
├── ARCHITECTURE.md                 # Technical design
├── IMPLEMENTATION_PLAN.md          # Milestone tracking
├── TESTING_GUIDE.md               # Manual test procedures
├── MILESTONE_X_COMPLETION.md      # Milestone completion reports (optional)
└── [other supporting docs]
```

### Documentation Timing

**During Development:**

- Create PRD, Architecture, Implementation Plan before coding
- Update Implementation Plan as milestones complete
- Write completion reports for complex milestones (optional)

**After Phase Completion:**

- Update USER_GUIDE.md with new features
- Update TROUBLESHOOTING.md with solutions found
- Update API_SPECIFICATION.md if APIs added
- Create phase completion summary (optional)

**At Release:**

- Write RELEASE_NOTES.md in release folder
- Update CHANGELOG.md with all changes
- Move phase folders to `docs/releases/vX.X/`

---

## Phase Overlap Management

### Sibling Phases (Independent)

**When to Use:**

- Features are independent and don't depend on each other
- Can be developed in parallel by different developers
- Example: Phase 2 (Multi-character) and Phase 3 (Web search)

**Folder Structure:**

```
docs/technical/
├── phase2/              # Multi-character coordination
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── IMPLEMENTATION_PLAN.md
└── phase3/              # Web search integration
    ├── PRD.md
    ├── ARCHITECTURE.md
    └── IMPLEMENTATION_PLAN.md
```

**Git Strategy:**

- Separate branches: `phase2`, `phase3`
- Can be developed simultaneously
- Merge to main independently when complete

**Dependency Tracking:**

- Document in Implementation Plan if one phase must complete before another
- Example: "Phase 3 requires Phase 2 agent system to be complete"

### Sub-Phases (Dependent)

**When to Use:**

- Feature is extension or enhancement of parent phase
- Discovered during parent phase implementation
- Tightly coupled to parent functionality
- Example: Phase 2.5 (Advanced relationship tracking) builds on Phase 2

**Folder Structure:**

```
docs/technical/
└── phase2/                    # Multi-character coordination
    ├── PRD.md
    ├── ARCHITECTURE.md
    ├── IMPLEMENTATION_PLAN.md
    └── phase2.5/              # Sub-phase: Relationship tracking
        ├── PRD.md
        ├── ARCHITECTURE.md
        └── IMPLEMENTATION_PLAN.md
```

**Git Strategy:**

- Use same branch as parent: `phase2`
- Milestones from both phases committed to same branch
- Tag sub-phase completion: `phase2.5-complete`
- Tag parent phase when both complete: `phase2-complete`

**When to Choose Sub-Phase vs New Phase:**

- **Sub-phase (2.5)** if:
  - Cannot function without parent phase
  - Extends parent functionality
  - Discovered during parent development
- **New phase (3)** if:
  - Independent feature
  - Could be built in different order
  - Stands alone conceptually

---

## Release Process

### Creating a Release

Follow these steps when multiple phases are ready to ship:

1. **Ensure All Phases Complete**
   - All milestones finished
   - All tests passing
   - Manual testing documented
   - Phase tags created

2. **Create Release Folder**

   ```bash
   mkdir -p docs/releases/v2.0
   ```

3. **Move Phase Folders**

   ```bash
   mv docs/technical/phase2 docs/releases/v2.0/
   mv docs/technical/phase3 docs/releases/v2.0/
   ```

4. **Create Release Notes**
   - File: `docs/releases/v2.0/RELEASE_NOTES.md`
   - Summarize all features from included phases
   - Highlight breaking changes
   - Document migration steps if needed
   - Include testing performed

5. **Update CHANGELOG.md**
   - Add new version section
   - Categorize changes: Added, Changed, Fixed, Removed
   - Link to release notes and phase docs

6. **Create Git Tag**

   ```bash
   git tag v2.0.0 -m "Release v2.0: Multi-character panel"
   git push --tags
   ```

7. **Merge to Main** (if not already done)

   ```bash
   git checkout main
   git merge phase2 --no-ff
   git merge phase3 --no-ff
   git push
   ```

### Release Folder Structure

```
docs/releases/
├── v1.0/
│   ├── RELEASE_NOTES.md
│   └── phase1/
│       ├── PRD.md
│       ├── ARCHITECTURE.md
│       └── ...
├── v1.5/
│   ├── RELEASE_NOTES.md
│   └── phase1.5/
│       ├── PRD.md
│       ├── ARCHITECTURE.md
│       └── ...
└── v2.0/
    ├── RELEASE_NOTES.md
    ├── phase2/
    │   └── ...
    └── phase3/
        └── ...
```

---

## Example: Phase 1.5 (Observability & Testing Tools)

Phase 1.5 serves as a reference implementation of this development process.

### What Was Built

#### Phase 1.5: Observability & Testing Tools

- 7 milestones completed over ~2 weeks
- Full developer dashboard for inspecting system state
- Released as v1.5.0

**Milestones:**

1. Foundation & Data Access
2. Story Beat Tool
3. Memory Tool
4. User Testing Tool
5. Tool Calls Inspection
6. Memory Extraction & Retrieval
7. Character Tool

### Artifacts Created

- ✅ PRD: [docs/technical/phase1.5/PRD.md](../technical/phase1.5/PRD.md)
- ✅ Architecture: [docs/technical/phase1.5/ARCHITECTURE.md](../technical/phase1.5/ARCHITECTURE.md)
- ✅ Implementation Plan: [docs/technical/phase1.5/IMPLEMENTATION_PLAN.md](../technical/phase1.5/IMPLEMENTATION_PLAN.md)
- ✅ Testing Guide: [docs/technical/phase1.5/MILESTONE5_TESTING_GUIDE.md](../technical/phase1.5/MILESTONE5_TESTING_GUIDE.md)
- ✅ Completion Reports: Multiple MILESTONE_X_COMPLETION.md files

### Git History

```bash
# Branch created
git checkout -b phase1.5

# Milestones committed
git commit -m "Complete Milestone 4: User Testing Tool"
git commit -m "Complete Milestone 5: Tool Calls Inspection"
git commit -m "Complete Milestone 6: Memory Extraction & Retrieval"
git commit -m "Complete Milestone 7: Character Tool"

# Phase tagged
git tag phase1.5-complete
```

### Testing Approach

- **E2E Tests:** Shell scripts in `tests/scripts/` (Playwright adopted mid-phase)
- **Manual Testing:** Documented in implementation plan and testing guides
- **AI Validation:** AI executed tests and created completion reports

### Lessons Applied to This Process

- Documentation before code prevents scope creep
- Milestone-level commits maintain clear history
- E2E tests provide most value early in project
- AI validation helps catch integration issues

---

## Quick Reference

### Starting a New Phase

```bash
# 1. Create phase folder from template
cp -r docs/templates/PHASE_TEMPLATE docs/technical/phase2

# 2. Fill out phase documents
# - Edit PRD.md
# - Edit ARCHITECTURE.md
# - Edit IMPLEMENTATION_PLAN.md
# - Edit TESTING_GUIDE.md

# 3. Create phase branch
git checkout -b phase2

# 4. Start implementing milestones
```

### Completing a Milestone

```bash
# 1. Verify completion checklist
# - Code works
# - E2E tests passing
# - AI validated
# - Manual test instructions documented

# 2. Update Implementation Plan
# - Mark milestone as complete
# - Add completion date
# - Document any blockers/discoveries

# 3. Commit milestone
git add .
git commit -m "Complete Milestone X: [Name] for Phase 2

[Description]

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Completing a Phase

```bash
# 1. Verify all milestones done
# 2. Run all E2E tests
npm run test:e2e

# 3. Complete manual testing
# Follow TESTING_GUIDE.md

# 4. Tag phase
git tag phase2-complete
git push --tags

# 5. Optional: Merge to main
git checkout main
git merge phase2 --no-ff
git push
```

### Creating a Release

```bash
# 1. Create release folder
mkdir -p docs/releases/v2.0

# 2. Move phase folders
mv docs/technical/phase2 docs/releases/v2.0/

# 3. Write release notes
# Create docs/releases/v2.0/RELEASE_NOTES.md

# 4. Update CHANGELOG.md
# Add version section with all changes

# 5. Create git tag
git tag v2.0.0 -m "Release v2.0: [Name]"
git push --tags
```

---

## Templates

All phase templates are available in:

- **Location:** `docs/templates/PHASE_TEMPLATE/`
- **Files:** PRD.md, ARCHITECTURE.md, IMPLEMENTATION_PLAN.md, TESTING_GUIDE.md

See individual template files for detailed structure and guidance.

---

## Changelog

### 1.0 - 2026-01-29

- Initial version documenting three-layer structure
- Git workflow defined
- Testing strategy established
- Phase 1.5 included as reference example

---

**Document Owner:** Development Team
**Review Cycle:** Updated as process evolves
**Questions:** See open questions in active phase PRDs

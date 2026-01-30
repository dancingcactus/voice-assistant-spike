# Phase Template

This folder contains templates for creating new phase documentation following the standardized development process.

## Overview

When starting a new phase (e.g., Phase 2, Phase 3, Phase 2.5), copy this entire folder and fill in the templates with your phase-specific information.

## Template Files

### 1. PRD.md (Product Requirements Document)

**Purpose:** Define what we're building and why

**When to create:** Before any coding begins

**Key sections:**

- Executive summary and success metrics
- User experience goals
- Functional and non-functional requirements
- User scenarios and acceptance criteria
- Scope (what's included and excluded)
- Open questions and risks

**Fill-in approach:**

- Replace `[Phase Name]` with actual phase name (e.g., "Multi-Character Coordination")
- Replace all `[placeholders]` with specific content
- Delete example text and replace with actual requirements
- Keep structure intact but adjust sections as needed

---

### 2. ARCHITECTURE.md (Technical Architecture)

**Purpose:** Define how we'll build it

**When to create:** After PRD is approved, before coding begins

**Key sections:**

- System overview and design principles
- Component architecture with diagrams
- Data models and storage strategy
- API endpoints and contracts
- Integration points
- Technology stack and dependencies

**Fill-in approach:**

- Use PRD as source of requirements
- Define technical approach for each functional requirement
- Create diagrams for complex flows
- Specify all APIs and data models
- Document all design decisions and trade-offs

---

### 3. IMPLEMENTATION_PLAN.md (Milestone Tracking)

**Purpose:** Break work into milestones and track progress

**When to create:** After architecture is defined, before coding begins

**Key sections:**

- Milestone breakdown (what gets built in each)
- Completion checklists for each milestone
- Success criteria and testing requirements
- Timeline tracking (planned vs actual)
- Blockers and discoveries

**Fill-in approach:**

- Break phase into 2-5 milestones (target: 1-3 days each)
- For each milestone, list backend/frontend components and API endpoints
- Link to PRD (requirements) and Architecture (design)
- Update status as milestones progress
- Mark completion checklists as work is done

---

### 4. TESTING_GUIDE.md (Manual Testing Procedures)

**Purpose:** Document step-by-step testing instructions

**When to create:** During implementation, updated per milestone

**Key sections:**

- Prerequisites (services, data, environment)
- Test procedures for each milestone
- Expected vs actual results
- Integration and regression tests
- Troubleshooting guide

**Fill-in approach:**

- Write test procedures as features are implemented
- Include happy path, error handling, and edge cases
- Provide exact commands and expected outputs
- Document how AI will validate tests
- Update as edge cases are discovered

---

## How to Use These Templates

### Step 1: Copy Template Folder

```bash
# For sibling phase (e.g., Phase 2, Phase 3)
cp -r docs/templates/PHASE_TEMPLATE docs/technical/phase2

# For sub-phase (e.g., Phase 2.5)
cp -r docs/templates/PHASE_TEMPLATE docs/technical/phase2/phase2.5
```

### Step 2: Rename and Customize

```bash
cd docs/technical/phase2

# Open each file and:
# 1. Replace "Phase X" with "Phase 2" (or actual name)
# 2. Replace "[Phase Name]" with actual descriptive name
# 3. Update all [placeholders] with real content
# 4. Delete example text
```

### Step 3: Fill Out in Order

**Week 1: Planning**

1. Fill out PRD.md
   - Define requirements and user stories
   - Establish success metrics
   - Get stakeholder approval

2. Fill out ARCHITECTURE.md
   - Design technical approach
   - Define components and APIs
   - Document design decisions

3. Fill out IMPLEMENTATION_PLAN.md
   - Break into milestones
   - Estimate timeline
   - Set up completion checklists

**Week 2+: Implementation**
4. Fill out TESTING_GUIDE.md (per milestone)

- Write test procedures as features are built
- Document expected behavior
- Include troubleshooting steps

1. Update IMPLEMENTATION_PLAN.md (ongoing)
   - Mark milestones complete
   - Track actual vs planned time
   - Document blockers and discoveries

### Step 4: Create Git Branch

```bash
# Start phase branch
git checkout -b phase2

# Commit initial documentation
git add docs/technical/phase2/
git commit -m "Add Phase 2: Multi-Character Coordination documentation

Created initial phase documentation:
- PRD with requirements and user stories
- Architecture with component design
- Implementation plan with 4 milestones
- Testing guide template

Ready to begin Milestone 1 implementation.

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Template Structure

```
PHASE_TEMPLATE/
├── README.md                   # This file - usage instructions
├── PRD.md                      # Product requirements (what & why)
├── ARCHITECTURE.md             # Technical design (how)
├── IMPLEMENTATION_PLAN.md      # Milestones and tracking
└── TESTING_GUIDE.md            # Manual test procedures
```

## Examples

See [Phase 1.5](../../technical/phase1.5/) for a real-world example of these templates in use.

**What to reference:**

- [PRD.md](../../technical/phase1.5/PRD.md) - Observability tools requirements
- [ARCHITECTURE.md](../../technical/phase1.5/ARCHITECTURE.md) - FastAPI + React design
- [IMPLEMENTATION_PLAN.md](../../technical/phase1.5/IMPLEMENTATION_PLAN.md) - 7 milestones tracked
- Various TESTING_GUIDE.md and completion reports

## Tips for Success

### Do's ✅

- **Fill out PRD before coding** - Prevents scope creep
- **Link between documents** - PRD ↔ Architecture ↔ Implementation Plan
- **Update as you go** - Mark milestones complete, document discoveries
- **Be specific** - Use real examples, not abstract descriptions
- **Keep it concise** - Focus on decisions and requirements, not obvious details
- **Use checklists** - Completion criteria should be checkable

### Don'ts ❌

- **Don't skip planning** - Tempting to jump to code, but costs time later
- **Don't make it perfect** - Good enough to start coding is good enough
- **Don't let it get stale** - Update during implementation, not after
- **Don't copy-paste blindly** - Adapt templates to your phase's needs
- **Don't ignore [placeholders]** - Replace all bracketed text with real content

## Template Customization

These templates are **starting points**, not rigid requirements. Feel free to:

- Add sections relevant to your phase
- Remove sections that don't apply
- Adjust structure for your needs
- Create additional documents (e.g., data migration guides)

**Key principle:** Templates should help, not hinder. Adapt them as needed.

## Questions?

See [DEVELOPMENT_PROCESS.md](../../DEVELOPMENT_PROCESS.md) for:

- Complete development methodology
- Git workflow details
- Testing strategy
- Release process

---

**Last Updated:** 2026-01-29
**Template Version:** 1.0
**Maintained By:** Development Team

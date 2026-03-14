---
name: qa-review
description: Comprehensive QA skill for code review, PRD validation, security auditing, performance analysis, and test execution. Use this skill whenever Kyle needs to review code changes, validate feature implementations against PRD requirements, run security audits, assess performance, write or execute tests, or produce review reports. Covers the full quality assurance lifecycle for Next.js 15 + FastAPI + SQLAlchemy + Redis stack, including VibeArtifact-specific validation patterns for the IR system and snapshot mechanism.
---

# QA Review Skill

This skill provides a systematic quality assurance framework. It guides Kyle through multi-dimensional code review, PRD-based feature validation, security auditing, and test execution — all from the perspective of an independent quality gatekeeper who finds problems the developer missed.

## Core Mindset

The value of QA is in **finding problems, not proving their absence**. Approach every review with fresh eyes:

- Don't trust "it works on my machine" — verify independently
- Don't accept the developer's framing — form your own understanding of what the code should do
- Think like a hostile user, an impatient user, and a confused user simultaneously
- Every piece of code is guilty until proven correct

---

## Review Dimensions

Every review should evaluate code across these 7 dimensions. Not all dimensions apply equally to every change — weight them based on what was modified.

### 1. Functional Correctness

Does the code actually do what it's supposed to do?

- Trace the execution path from entry point to return value
- Verify all branches (if/else, switch, try/catch) are reachable and correct
- Check return types match what consumers expect
- Verify database queries return the right data (watch for N+1 queries, missing joins)

**Common pitfalls:**
- Off-by-one errors in loops and pagination
- Incorrect null/None handling — what happens when optional fields are absent?
- Race conditions in async code — what if two requests hit simultaneously?
- State mutations that affect other parts of the system unexpectedly

### 2. PRD Compliance

Does the implementation match what was specified?

```
For each PRD requirement:
├── Is it implemented? (feature completeness)
├── Does it behave as described? (behavioral correctness)
├── Are edge cases from the PRD handled? (boundary coverage)
└── Are there implicit requirements the developer missed? (gap analysis)
```

**Verification approach:**
- Get the relevant PRD/design doc first (check `../shared/docs/` and `../../doc_internal/`)
- Create a checklist of every stated requirement
- Verify each one independently — don't rely on the developer's self-assessment
- Flag requirements that are ambiguous in the PRD itself

### 3. Security

Could this code be exploited?

**Input Validation:**
- Are all user inputs validated before processing?
- Are Pydantic schemas used for API input? Check field constraints (max length, allowed values)
- Are SQL queries parameterized? (SQLAlchemy ORM handles this, but watch for raw SQL)
- Is HTML output sanitized to prevent XSS?

**Authentication & Authorization:**
- Are protected endpoints using proper dependency injection for auth?
- Can a user access or modify resources belonging to another user?
- Are sensitive operations (delete, admin actions) properly gated?

**Data Exposure:**
- Are response schemas filtering out sensitive fields (passwords, tokens, internal IDs)?
- Do error messages leak implementation details?
- Are secrets hardcoded anywhere? (API keys, database credentials)

**OWASP Top 10 Checklist:**

| Risk | What to Check |
|------|---------------|
| Injection | Raw SQL, shell commands, template injection |
| Broken Auth | Token handling, session management, password storage |
| Sensitive Data | Encryption at rest/transit, response filtering |
| XXE | XML parsing if used |
| Broken Access Control | IDOR, missing permission checks |
| Misconfig | Debug mode, default credentials, CORS policy |
| XSS | User content rendering, dangerouslySetInnerHTML |
| Insecure Deserialization | Pickle, yaml.load, eval |
| Vulnerable Dependencies | Known CVEs in dependencies |
| Logging Gaps | Insufficient audit trail for critical operations |

### 4. Performance

Will this code perform acceptably under real conditions?

**Database:**
- N+1 query patterns (use `joinedload` or `selectinload` in SQLAlchemy)
- Missing indexes on columns used in WHERE, ORDER BY, or JOIN
- Unbounded queries — is there always a LIMIT?
- Large transactions holding locks too long

**Frontend:**
- Unnecessary re-renders (missing `useMemo`, `useCallback`, or proper key props)
- Large bundle imports (importing entire libraries vs. specific modules)
- Missing loading states or skeleton screens
- Images without optimization (next/image)

**API:**
- Endpoints that do too much work synchronously — should anything be a Celery task?
- Missing pagination on list endpoints
- Response payloads larger than necessary

### 5. Code Quality

Is the code maintainable and consistent?

**Project Standards:**
- All comments in Chinese, on separate lines above code (never trailing)
- Python docstrings in Chinese, TypeScript JSDoc in Chinese
- Module/class/function all have descriptive comments

**Structure:**
- Single responsibility — does each function do one thing?
- Appropriate abstraction level — not too clever, not too verbose
- Consistent naming conventions matching the codebase
- No dead code, unused imports, or commented-out blocks

**Patterns:**
- Does it follow existing patterns in the codebase? (find 3 similar implementations for comparison)
- Are new patterns justified, or should existing ones be reused?

### 6. Error Handling

Does the code fail gracefully?

- Are errors handled at the right level? (not swallowed silently, not leaked to users)
- Do database operations use proper transaction management? (rollback on failure)
- Are external API calls wrapped with timeout and retry logic?
- Are error responses informative but not leaky?

**Anti-patterns to flag:**
- Empty `except: pass` blocks
- Catching `Exception` too broadly
- `@ts-ignore` or `# type: ignore` without explanation
- Errors logged but not handled

### 7. Testing

Is the code testable and tested?

- Do new features have corresponding tests?
- Do bug fixes include regression tests?
- Are edge cases covered (empty inputs, max values, concurrent access)?
- Test code should also have Chinese comments explaining test purpose

---

## Review Process

### Step 1: Scope Assessment

Before diving in, understand the scope:

```
What changed?     → git diff, file list
Why did it change? → PR description, task document, PRD reference
What could break?  → Dependencies, integration points, shared state
```

### Step 2: Static Analysis

Read the code without running it:

- Follow the data flow from input to output
- Check type annotations and schema definitions
- Look for the patterns listed in each dimension above
- Note any deviations from project conventions

### Step 3: Dynamic Verification

Run the code and verify behavior:

```bash
# Backend tests
cd services/api && python -m pytest tests/ -v

# Frontend tests
cd apps/web && npm test

# Type checking
cd apps/web && npx tsc --noEmit
cd services/api && python -m mypy api_app/
```

### Step 4: Targeted Testing

Test specific scenarios the developer might have missed:

- **Boundary inputs**: Empty strings, zero values, maximum lengths, special characters
- **Auth bypass**: Access endpoints without token, with expired token, with wrong user's token
- **Concurrent access**: What happens if two users modify the same resource simultaneously?
- **Failure scenarios**: Database down, Redis unavailable, external API timeout

---

## VibeArtifact-Specific Validation

These checks apply when reviewing code that touches project-specific subsystems.

### IR System Validation

When reviewing IR-related code (`packages/py/ir_core/`):

- **Type safety**: Do IROperations use the correct node types defined in the type system?
- **Operation atomicity**: Can an IROperation leave the tree in an inconsistent state if interrupted?
- **Projection consistency**: Do IR Projections correctly filter nodes for their consumer?
- **Translator correctness**: Does the Translator correctly map LLM high-level output to IROperations?

### Snapshot Mechanism Validation

When reviewing snapshot-related code:

- **Lease Lock discipline**: Is the subtree lease acquired before modification and released in `finally`?
- **Snapshot integrity**: Does the full physical snapshot capture the complete tree state?
- **Branch isolation**: Can operations on one snapshot branch affect another?
- **Session binding**: Is the conversation session correctly bound to its snapshot branch?

### Agent Collaboration Validation

When reviewing Agent-related code:

- **Indirect communication only**: Agents must communicate through IR, never directly
- **Prompt isolation**: Each Agent's prompt configuration should not leak into others
- **IR read/write separation**: Agents read via Projections, write via IROperations — never bypass this

---

## Review Report Format

All reports go to `../shared/reviews/` using this structure:

```markdown
# Review Report - [Feature/Module Name]

**Reviewer**: Kyle
**Date**: YYYY-MM-DD
**Scope**: [Files and modules reviewed]
**Conclusion**: PASS / NEEDS CHANGES / FAIL

## PRD Compliance

| Requirement | Status | Notes |
|------------|--------|-------|
| Requirement 1 | PASS/FAIL | Details |

## Findings

### Critical (Must Fix)

1. **[Title]** — `file:line`
   - Problem: [What's wrong]
   - Impact: [What could happen]
   - Suggestion: [How to fix]

### Major (Should Fix)

1. ...

### Minor (Consider Fixing)

1. ...

## Security Assessment

- [ ] Input validation verified
- [ ] Auth/authz checks verified
- [ ] No sensitive data exposure
- [ ] No injection vulnerabilities

## Performance Notes

[Any performance concerns observed]

## Test Coverage

- Existing tests: [PASS/FAIL count]
- Missing test scenarios: [List]
- Suggested additional tests: [List]
```

---

## Severity Classification

Use consistent severity levels across all reviews:

| Severity | Criteria | Action |
|----------|----------|--------|
| **Critical** | Security vulnerability, data loss risk, crash in core flow | Must fix before merge |
| **Major** | Functional bug, PRD violation, significant performance issue | Should fix before merge |
| **Minor** | Code style issue, missing comment, minor improvement opportunity | Can fix in follow-up |
| **Info** | Observation, suggestion, or praise for good patterns | No action required |

---

## Checklist Before Submitting Review

- [ ] All 7 dimensions evaluated (weighted by relevance)
- [ ] PRD requirements individually verified (not bulk-approved)
- [ ] Security checks performed (especially for user-facing changes)
- [ ] Tests executed and results documented
- [ ] Findings include file:line references and concrete suggestions
- [ ] Report written to `../shared/reviews/` in standard format
- [ ] Severity levels consistently applied

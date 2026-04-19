---
name: refactor-arch
description: Use when auditing or refactoring a codebase to MVC architecture — detects code smells, anti-patterns, SOLID violations, and hardcoded credentials across any language or framework, then restructures the project into clean Model-View-Controller layers with validation
---

# refactor-arch

## Overview

Technology-agnostic skill that audits and refactors any project to MVC architecture in three sequential phases: analyze the stack, audit against a catalog of anti-patterns, then refactor and validate.

**BLOCKING REQUIREMENT:** Phase 2 MUST pause and ask for user confirmation before modifying any file.

## Three Phases

### Phase 1 — Project Analysis

Use heuristics from `project-analysis.md` to detect and print:
- Language, framework, and version
- Database type and tables/collections
- Current architecture pattern (monolith, layered, flat, etc.)
- Number of source files and approximate lines of code
- Domain areas (e.g., users, products, orders)

Output format:
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <lang>
Framework:     <framework + version>
Dependencies:  <key deps>
Domain:        <business domain>
Architecture:  <current architecture description>
Source files:  <N> files analyzed
DB tables:     <table/collection list>
================================
```

### Phase 2 — Architecture Audit

1. Cross every source file against the anti-patterns in `anti-patterns-catalog.md`
2. For each finding, record: severity, file path, exact line number(s), description, impact, recommendation
3. Generate audit report at `reports/audit-project.md` using the template in `audit-report-template.md`
4. Print summary to terminal
5. **STOP. Ask: "Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]"**
6. Only continue if user answers `y`

Severity scale (see `anti-patterns-catalog.md` for full definitions):
- **CRITICAL**: Architecture failures, security exposure, God Classes
- **HIGH**: MVC/SOLID violations that block testability
- **MEDIUM**: Duplication, N+1 queries, missing validation
- **LOW**: Naming, magic numbers, readability

### Phase 3 — Refactoring

1. Restructure project following rules in `mvc-guidelines.md`
2. Apply transformation patterns from `refactoring-playbook.md` for each finding
3. Move all sensitive variables to environment variables using the `.env` pattern (see P2 in `refactoring-playbook.md`)
4. If the application startup command changed or a `.env` file is required, update `README.md` with instructions
5. Validate the result:
   - Boot the application without errors
   - Verify all endpoints respond correctly
   - Confirm zero remaining anti-patterns

Output format:
```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<tree of new structure>

Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Reference Files

| File | Purpose |
|------|---------|
| `project-analysis.md` | Heuristics for detecting language, framework, database, and architecture |
| `anti-patterns-catalog.md` | 15 anti-patterns with detection signals and severity (CRITICAL→LOW) |
| `audit-report-template.md` | Standardized audit report format |
| `mvc-guidelines.md` | Target MVC layer rules (Models, Views/Routes, Controllers) |
| `refactoring-playbook.md` | Before/after transformation patterns for each anti-pattern |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Modifying files without confirmation | Always pause after Phase 2 and await `y` |
| Approximate line numbers | Report exact line numbers from the source |
| Skipping validation | Always boot the app and test endpoints after Phase 3 |
| Forcing a single language's MVC structure | Adapt structure to the framework's conventions |
| Overwriting reports/ without checking | Append new dated section if `reports/audit-project.md` already exists |
| Leaving sensitive variables hardcoded | Always move secrets to `.env` and add to `.gitignore` |
| Not updating README after structural changes | Update README.md whenever startup command or `.env` requirements change |

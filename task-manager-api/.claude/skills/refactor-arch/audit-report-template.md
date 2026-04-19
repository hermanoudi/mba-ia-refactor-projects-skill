# Audit Report Template

Save this report to `reports/audit-project.md`. If the file already exists, append a new dated section rather than overwriting.

---

```markdown
# Architecture Audit Report

**Project:** <project name>
**Date:** <YYYY-MM-DD>
**Stack:** <language> + <framework>
**Files Analyzed:** <N> | **Lines of Code:** ~<N>
**Audited By:** refactor-arch skill

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | <N>   |
| HIGH     | <N>   |
| MEDIUM   | <N>   |
| LOW      | <N>   |
| **TOTAL**| **<N>** |

---

## Findings

### [CRITICAL] <Anti-Pattern Name>
**File:** `<path/to/file.ext>:<line_start>-<line_end>`  
**Description:** <What is wrong and where exactly>  
**Impact:** <Why this matters — testability, security, maintainability>  
**Recommendation:** <Specific action to fix it>

---

### [HIGH] <Anti-Pattern Name>
**File:** `<path/to/file.ext>:<line>`  
**Description:** <What is wrong>  
**Impact:** <Why this matters>  
**Recommendation:** <Specific action>

---

<!-- Repeat block for each finding, grouped by severity: CRITICAL → HIGH → MEDIUM → LOW -->

---

## Proposed MVC Structure

```
src/
├── config/
│   └── settings.<ext>
├── models/
│   └── <domain>_model.<ext>
├── controllers/
│   └── <domain>_controller.<ext>
├── views/          # or routes/
│   └── <domain>_routes.<ext>
├── middlewares/
│   └── error_handler.<ext>
└── app.<ext>        # composition root
```

---

## Next Step

Run Phase 3 to refactor automatically, or address findings manually.
```

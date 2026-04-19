# Anti-Patterns Catalog

## Severity Definitions

| Severity | Criteria |
|----------|----------|
| CRITICAL | Serious architecture or security failures that prevent correct functioning, expose sensitive data (e.g., hardcoded credentials, SQL Injection), or completely violate separation of responsibilities (e.g., "God Class" containing database access, complex business logic, and routing in the same file) |
| HIGH | Strong violations of MVC pattern or SOLID principles that severely hinder maintenance and testing (e.g., heavy business logic trapped inside Controllers, tight coupling without Dependency Injection, or mutable global state used across the application) |
| MEDIUM | Standardization issues, code duplication, or moderate performance bottlenecks (e.g., N+1 queries against the database, improper middleware usage, missing route validation) |
| LOW | Readability improvements, poor variable naming, or magic numbers scattered through the code |

---

## CRITICAL

### C1 — God Class / God Module
**Signal:** Single file/class handles DB queries, business logic, validation, and routing for 3+ domains.  
**Detection:** File > 200 lines mixing SQL/ORM calls with HTTP response construction.  
**Fix:** Split by domain into dedicated model, controller, and route files.

### C2 — Hardcoded Credentials / Secrets
**Signal:** Secret keys, passwords, API keys, or DB connection strings embedded in source code.  
**Detection:** Regex patterns — `SECRET_KEY\s*=\s*['"][^'"]{6,}`, `password\s*=\s*['"]`, `api_key\s*=\s*['"]`.  
**Fix:** Move to environment variables or a secrets manager; add to `.gitignore`.

### C3 — SQL Injection / Unparameterized Queries
**Signal:** User input concatenated directly into SQL strings.  
**Detection:** `cursor.execute("... " + variable)` or f-strings inside execute calls.  
**Fix:** Use parameterized queries or ORM methods exclusively.

### C4 — Zero Layer Separation (Flat Architecture)
**Signal:** All application logic lives in a single entry-point file (e.g., `app.py`, `index.js`).  
**Detection:** Route definitions, DB calls, and business logic all in one file with no imports to domain modules.  
**Fix:** Introduce MVC directory structure per `mvc-guidelines.md`.

---

## HIGH

### H1 — Business Logic in Controller
**Signal:** Controller/route handler contains complex calculations, data transformation, or multi-step workflows that belong in a service or model layer.  
**Detection:** Route handler > 30 lines; contains loops, conditionals over domain objects, or direct DB access.  
**Fix:** Extract logic to a dedicated service or model method; controller calls it and returns the result.

### H2 — No Dependency Injection (Hard Coupling)
**Signal:** Classes instantiate their dependencies internally (`db = Database()` inside constructor).  
**Detection:** `new`/direct constructor calls inside class methods for infrastructure dependencies.  
**Fix:** Pass dependencies via constructor parameters or a DI container.

### H3 — Global Mutable State
**Signal:** Module-level variables modified by multiple routes/functions, causing race conditions and hidden coupling.  
**Detection:** Variables defined at module scope that are assigned (`=`) inside functions.  
**Fix:** Encapsulate state in a class or use request-scoped context (e.g., Flask's `g`).

### H4 — Deprecated API Usage
**Signal:** Use of framework APIs, library methods, or language features flagged as deprecated in the current version.  
**Detection:** Import or call matches known deprecated symbol list (e.g., `before_first_request` in Flask ≥ 2.3, `request.data` as primary body parser, Node.js `url.parse`).  
**Fix:** Replace with the recommended modern alternative per the library's migration guide.

### H5 — Missing Interface / Abstraction Layer (SOLID — Dependency Inversion)
**Signal:** High-level business logic directly imports and uses low-level infrastructure (DB, HTTP client, filesystem).  
**Detection:** Business functions import database drivers or ORM models directly with no abstraction.  
**Fix:** Introduce a repository or gateway interface between business logic and infrastructure.

---

## MEDIUM

### M1 — N+1 Query Problem
**Signal:** A query is executed inside a loop, causing O(n) database round-trips.  
**Detection:** ORM query call (`.find()`, `.query()`, `.execute()`) inside a `for`/`while` loop over a result set.  
**Fix:** Use eager loading (`.include()`, `JOIN`, `select_related`) or batch queries.

### M2 — Missing Input Validation
**Signal:** Route handlers use request body/params directly without validation or sanitization.  
**Detection:** `request.json`, `req.body`, `request.args` accessed without schema validation middleware or explicit checks.  
**Fix:** Add validation schema at route entry point (e.g., Marshmallow, Joi, Pydantic, Zod).

### M3 — Improper Error Handling
**Signal:** Bare `except Exception` / `catch (e)` that swallows errors silently or leaks stack traces to the client.  
**Detection:** Broad catch blocks with no logging and direct `return str(e)` to HTTP response.  
**Fix:** Add structured error handler middleware; log internally, return safe error messages externally.

---

## LOW

### L1 — Magic Numbers / Magic Strings
**Signal:** Numeric literals or string constants with business meaning scattered through code.  
**Detection:** Numeric literals (not 0 or 1) and uppercase-heavy strings in business logic without named constants.  
**Fix:** Extract to named constants or configuration values.

### L2 — Poor Naming
**Signal:** Single-letter variables, overly abbreviated names, or names that don't express intent.  
**Detection:** Variables `a`, `b`, `x`, `temp`, `data2`, function names like `do_thing()`.  
**Fix:** Rename to express the domain concept clearly.

### L3 — Dead Code
**Signal:** Functions, imports, or variables that are defined but never referenced.  
**Detection:** Unused imports (linter warnings), functions with no call sites in the codebase.  
**Fix:** Delete dead code; use linter auto-fix where available.

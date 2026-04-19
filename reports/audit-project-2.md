# Architecture Audit Report

**Project:** ecommerce-api-legacy (LMS with e-commerce)  
**Date:** 2026-04-19  
**Stack:** Node.js + Express.js  
**Files Analyzed:** 3 | **Lines of Code:** ~180  
**Audited By:** refactor-arch skill

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2     |
| HIGH     | 5     |
| MEDIUM   | 3     |
| LOW      | 3     |
| **TOTAL**| **13**|

---

## Findings

### [CRITICAL] C2 — Hardcoded Credentials / Secrets

**File:** `src/utils.js:1-7`  
**Description:** Database user, password, payment gateway key, and SMTP credentials are hardcoded directly in source code. These sensitive values are exposed in version control and any code dump/leak.  
**Impact:** Complete security breach — attackers can access production databases, intercept payments, and send unauthorized emails. Violates PCI-DSS compliance and data protection regulations.  
**Recommendation:** Move all credentials to environment variables (.env file, not committed). Use `process.env.DB_USER`, `process.env.PAYMENT_GATEWAY_KEY`, etc. Add `.env` to `.gitignore`.

---

### [CRITICAL] C1 — God Class / God Module

**File:** `src/AppManager.js:4-138`  
**Description:** Single `AppManager` class handles database initialization, route definition, business logic for checkout, financial reporting, user deletion, and response serialization. No separation of concerns: all three domains (users, courses, payments) live in one file.  
**Impact:** Impossible to test individual routes without instantiating the entire manager. Changes to checkout logic require modifying the same file as user deletion. New developers cannot understand the flow. Cannot reuse business logic across endpoints.  
**Recommendation:** Split into: `UserModel`, `CourseModel`, `PaymentModel`, `CheckoutController`, `AdminController`, and separate route files (`user_routes.js`, `checkout_routes.js`, `admin_routes.js`).

---

### [HIGH] H2 — No Dependency Injection (Hard Coupling)

**File:** `src/AppManager.js:5-7` (constructor)  
**Description:** Database is instantiated directly in the constructor (`this.db = new sqlite3.Database(':memory:')`), creating hard coupling. Cannot swap with a mock database for testing or change database type without modifying the class.  
**Impact:** Unit testing is impossible — every test must use a real SQLite in-memory database. Cannot test the checkout logic independently from DB I/O. Cannot reuse AppManager with a different database.  
**Recommendation:** Inject database as a constructor parameter: `constructor(db) { this.db = db; }`. Pass a real or mock database from `app.js`.

---

### [HIGH] H1 — Business Logic in Controller

**File:** `src/AppManager.js:28-78` (POST /api/checkout route)  
**Description:** Route handler contains business logic: card validation (checking if card starts with "4"), enrollment creation, payment processing, and audit logging. A 51-line function mixing HTTP concerns with domain logic.  
**Impact:** Business logic is trapped inside a route definition, making it untestable and unreusable. Cannot apply this checkout logic to a batch enrollment flow or a CLI tool.  
**Recommendation:** Extract a `CheckoutService.checkout(userId, courseId, card)` method. The route becomes: validate input → call service → return response.

---

### [HIGH] H3 — Global Mutable State

**File:** `src/utils.js:9-10` and used in `src/AppManager.js:59`  
**Description:** Module exports `globalCache` and `totalRevenue` — both are modified at module scope by route handlers. `globalCache` is written by `logAndCache()` called from the checkout route. Race conditions occur if two requests run concurrently.  
**Impact:** In production with multiple concurrent requests, cache state becomes unpredictable. `totalRevenue` is exported but never incremented, indicating incomplete/abandoned feature.  
**Recommendation:** Encapsulate cache within a request-scoped session or class. Remove unused `totalRevenue`. If caching is needed, use Redis or request-local storage.

---

### [HIGH] H5 — Missing Interface / Abstraction Layer (SOLID — Dependency Inversion)

**File:** `src/AppManager.js` (entire file)  
**Description:** All route handlers directly call `this.db.run()` and `this.db.get()` (raw SQLite API). No repository or service layer abstracts database access. Business logic tightly coupled to database implementation details.  
**Impact:** Cannot switch from SQLite to PostgreSQL without rewriting every route handler. Business logic is not reusable in different contexts (e.g., batch processing, APIs). Hard to test and debug data access patterns.  
**Recommendation:** Create a `UserRepository`, `CourseRepository`, `PaymentRepository` that encapsulate all database access. Routes call repositories, which are injected.

---

### [HIGH] H4 — Deprecated API Usage

**File:** `src/AppManager.js:43-78` (nested callback hell)  
**Description:** Heavy use of callback-based async patterns (SQLite with callback functions). While not technically deprecated in Express.js, callbacks are considered outdated in modern Node.js (Promise/async-await style is standard). Makes the code hard to read and error-prone.  
**Impact:** Deep nesting ("callback hell") makes code difficult to follow. Error handling is scattered across multiple nested callbacks. Harder to reason about execution flow.  
**Recommendation:** Modernize to async/await by wrapping SQLite calls in Promises, or migrate to a Promise-based database driver (e.g., `better-sqlite3` with sync API, or use `sqlite` with Promises).

---

### [MEDIUM] M1 — N+1 Query Problem

**File:** `src/AppManager.js:89-127` (GET /api/admin/financial-report)  
**Description:** For each course, the code queries enrollments (1 query). For each enrollment, it queries the student user (1 query) and then the payment (1 query per enrollment). With 10 courses, 50 enrollments → 10 + 50 + 50 = 110 queries instead of 1 JOIN query.  
**Impact:** Severe performance degradation as data grows. Database is hit thousands of times per report request. Locks and contention increase.  
**Recommendation:** Replace the loop-based queries with a single SQL JOIN: `SELECT c.*, e.*, u.name, u.email, p.amount, p.status FROM courses c LEFT JOIN enrollments e ON c.id=e.course_id LEFT JOIN users u ON e.user_id=u.id LEFT JOIN payments p ON e.id=p.enrollment_id`. Then iterate the result in-memory.

---

### [MEDIUM] M2 — Missing Input Validation

**File:** `src/AppManager.js:29-35` (POST /api/checkout)  
**Description:** Route only checks if fields exist (`!u || !e || !cid || !cc`), but does not validate type, format, or length. No email format validation, no credit card format check, no name validation. Request body is used directly without schema validation.  
**Impact:** Invalid data causes silent failures or crashes downstream. Missing `pwd` field is accepted (defaults to "123456" in line 68). Malformed JSON could cause application errors. No protection against malicious input.  
**Recommendation:** Add a validation middleware using `express-validator` or `joi`. Validate email format, password strength, card format (Luhn check), and course ID as integer.

---

### [MEDIUM] M3 — Improper Error Handling

**File:** `src/AppManager.js:38, 41, 51, 55, etc.` (error responses)  
**Description:** Error handlers return generic messages ("Erro DB", "Erro Matrícula", "Erro Pagamento") without logging. Errors are not logged to a system logger. No structured error format. Database errors are exposed directly to the client.  
**Impact:** Difficult to debug production issues. Clients cannot distinguish between user input errors and server errors. Database error details could leak sensitive information.  
**Recommendation:** Implement a centralized error handler middleware that logs errors internally and returns safe, structured responses: `{ error: "Internal server error", requestId: "xxx" }` to client.

---

### [LOW] L2 — Poor Naming

**File:** `src/AppManager.js:29-34` (POST /api/checkout route handler)  
**Description:** Variables use cryptic abbreviations: `u` (user), `e` (email), `p` (password), `cid` (course ID), `cc` (credit card). Makes the code difficult to read and understand intent.  
**Impact:** Reduced code readability. Increases chance of misuse or bugs during maintenance. Makes onboarding new developers harder.  
**Recommendation:** Rename to: `userName`, `email`, `password`, `courseId`, `cardNumber`.

---

### [LOW] L1 — Magic Numbers / Magic Strings

**File:** `src/utils.js:19` (badCrypto function)  
**Description:** The loop iteration `10000` is a magic number with no explanation. Why 10000? Is it a security constant? `0x4` in line 46 of AppManager (checking if card starts with "4") is also magic.  
**Impact:** Code is harder to understand. Future maintainers cannot reason about why these specific values were chosen. Makes tuning or debugging harder.  
**Recommendation:** Extract to named constants at the top of the file: `const HASH_ITERATIONS = 10000; const VISA_CARD_PREFIX = '4';`

---

### [LOW] L3 — Dead Code

**File:** `src/utils.js:10` and module.exports (line 25)  
**Description:** `totalRevenue` variable is declared and exported but never used anywhere in the codebase. It is initialized to `0` and never modified.  
**Impact:** Code clutter. Developers may wonder if this is incomplete functionality. Adds confusion during maintenance.  
**Recommendation:** Delete the unused variable.

---

## Proposed MVC Structure

```
src/
├── config/
│   └── settings.js          # Secrets from .env
├── models/
│   ├── user.model.js        # User data access
│   ├── course.model.js      # Course data access
│   ├── enrollment.model.js  # Enrollment data access
│   └── payment.model.js     # Payment data access
├── controllers/
│   ├── checkout.controller.js   # Checkout business logic
│   ├── admin.controller.js      # Admin/reporting logic
│   └── user.controller.js       # User management logic
├── routes/
│   ├── checkout.routes.js   # Checkout endpoints
│   ├── admin.routes.js      # Admin endpoints
│   └── user.routes.js       # User endpoints
├── middleware/
│   ├── validation.middleware.js # Input validation
│   └── error.handler.js          # Error handling
├── database/
│   └── db.js                # Database initialization (injected)
└── app.js                   # Entry point
```

---

## Next Step

**Phase 2 is complete.** The audit identifies 13 findings across all severity levels, with 2 CRITICAL issues requiring immediate action (exposed credentials and god class).

Proceed with Phase 3 to automatically refactor and validate the application? **[y/n]**

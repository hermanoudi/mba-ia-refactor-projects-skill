# Architecture Audit Report: task-manager-api

**Generated:** 2026-04-19  
**Project:** Task Manager API (Flask/Python)  
**Total Issues Found:** 13

---

## Executive Summary

The task-manager-api project demonstrates partial MVC architecture (models/, routes/, services/, utils/) but contains **2 CRITICAL security issues**, **2 HIGH architectural violations**, **3 MEDIUM quality issues**, and **6 LOW readability issues**. The most urgent concerns are hardcoded credentials and business logic leakage into route handlers, which severely impact maintainability and security.

---

## CRITICAL Issues

### C1 — Hardcoded Credentials / Secrets
**Severity:** CRITICAL  
**Pattern:** C2 (Hardcoded Credentials)  
**Files:** 
- `app.py`, line 13
- `services/notification_service.py`, lines 9-10

**Description:**  
Secret application key and email credentials are hardcoded directly in source code:
- `app.py:13`: `SECRET_KEY = 'super-secret-key-123'`
- `services/notification_service.py:9-10`: `email_user = 'taskmanager@gmail.com'` and `email_password = 'senha123'`

**Impact:**  
- Exposed credentials in public/shared repositories
- Compromised application security and email account access
- Violation of OWASP guidelines and industry standards

**Recommendation:**  
Move all secrets to environment variables using `.env` file and `python-dotenv`:
- Use `os.environ.get('SECRET_KEY')` in `app.py`
- Use `os.environ.get('EMAIL_USER')` and `os.environ.get('EMAIL_PASSWORD')` in NotificationService
- Create `.env.example` with placeholder values
- Add `.env` to `.gitignore`

---

### C2 — Insecure Password Hashing (MD5)
**Severity:** CRITICAL  
**Pattern:** Security vulnerability (weak hashing)  
**File:** `models/user.py`, lines 27-32

**Description:**  
Passwords are hashed using MD5, an obsolete cryptographic hash vulnerable to rainbow table attacks and brute-force:
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

**Impact:**  
- User account compromise via leaked password databases
- Violates password security best practices (PCI DSS, GDPR)
- No salt applied, enabling dictionary attacks

**Recommendation:**  
Replace MD5 with bcrypt or Argon2:
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd, method='pbkdf2:sha256')

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

---

## HIGH Issues

### H1 — Business Logic in Route Handlers (Controllers)
**Severity:** HIGH  
**Pattern:** H1 (Business Logic in Controller)  
**Files:**
- `routes/task_routes.py`, lines 11-63 (get_tasks), lines 273-299 (task_stats)
- `routes/report_routes.py`, lines 12-101 (summary_report)
- `routes/user_routes.py`, lines 10-25 (get_users)

**Description:**  
Route handlers contain complex business logic that should reside in service layers:
- Overdue calculation logic duplicated across multiple routes (task_routes.py:30-39, user_routes.py:171-180, report_routes.py:34-43)
- Statistics aggregation (pending, done, cancelled counts) computed in route handlers
- User/category lookups performed inside loops without eager loading
- Serialization logic intertwined with business rules

**Impact:**  
- Difficult to test business logic in isolation
- Code duplication leads to maintenance inconsistencies
- Route handlers exceed 30-50 lines, becoming "fat controllers"
- Tight coupling between HTTP handling and domain logic

**Recommendation:**  
Extract to dedicated service classes:
- Create `TaskService` for task-related business logic
- Create `ReportService` for aggregation and statistics
- Create `UserService` for user-related queries
- Use services in route handlers for clean separation

Example refactoring:
```python
# In services/task_service.py
class TaskService:
    def get_all_tasks_with_enrichment(self):
        tasks = Task.query.all()
        return [self._enrich_task(t) for t in tasks]
    
    def _enrich_task(self, task):
        return {
            **task.to_dict(),
            'user_name': task.user.name if task.user else None,
            'category_name': task.category.name if task.category else None,
            'overdue': self._calculate_overdue(task)
        }
```

---

### H2 — Missing Abstraction / Dependency Injection
**Severity:** HIGH  
**Pattern:** H5 (Missing Interface/Abstraction Layer)  
**Files:** 
- `services/notification_service.py` (not injected)
- All route handlers (direct db access)

**Description:**  
- NotificationService is instantiated internally with hardcoded dependencies
- No repository pattern for data access abstraction
- Route handlers directly access Flask-SQLAlchemy ORM
- No dependency injection container or service locator

**Impact:**  
- Difficult to test (cannot mock database or email service)
- Tight coupling to specific ORM and email implementation
- Cannot swap implementations without code changes

**Recommendation:**  
Introduce repository pattern and dependency injection:
```python
# In services/repositories.py
class TaskRepository:
    def get_all(self):
        return Task.query.all()
    
    def get_by_id(self, task_id):
        return Task.query.get(task_id)

# In routes, inject repositories
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    task_repo = TaskRepository()
    service = TaskService(task_repo)
    tasks = service.get_all_with_enrichment()
    return jsonify(tasks), 200
```

---

## MEDIUM Issues

### M1 — N+1 Query Problem
**Severity:** MEDIUM  
**Pattern:** M1 (N+1 Query)  
**Files:**
- `routes/task_routes.py`, lines 41-48 (User.query.get inside loop)
- `routes/task_routes.py`, lines 50-57 (Category.query.get inside loop)
- `routes/task_routes.py`, lines 281-287 (Task.query.all in loop)
- `routes/report_routes.py`, lines 53-68 (User.query.all + Task.query filter inside loop)
- `routes/user_routes.py`, lines 14-24 (accessing u.tasks relationship)

**Description:**  
Database queries executed inside loops cause O(n) round-trips:

```python
# routes/task_routes.py:41-48 — PROBLEMATIC
for t in tasks:
    if t.user_id:
        user = User.query.get(t.user_id)  # Query per task!
```

```python
# routes/report_routes.py:53-68 — PROBLEMATIC
for u in users:
    user_tasks = Task.query.filter_by(user_id=u.id).all()  # Query per user!
```

**Impact:**  
- Severe performance degradation with large datasets
- Database connection pool exhaustion
- Scalability bottleneck

**Recommendation:**  
Use eager loading and SQL JOINs:

```python
# Use SQLAlchemy joinedload
from sqlalchemy.orm import joinedload

tasks = Task.query.options(
    joinedload(Task.user),
    joinedload(Task.category)
).all()

# Or use explicit JOIN
tasks = db.session.query(Task).outerjoin(User).outerjoin(Category).all()
```

---

### M2 — Bare Exception Handlers (Improper Error Handling)
**Severity:** MEDIUM  
**Pattern:** M3 (Improper Error Handling)  
**Files:**
- `routes/task_routes.py`, line 62
- `routes/task_routes.py`, line 237
- `routes/user_routes.py`, line 130
- `routes/report_routes.py`, lines 186, 208, 222

**Description:**  
Generic `except:` clauses without logging or specific exception handling:

```python
try:
    db.session.commit()
except:  # Too broad, no logging
    return jsonify({'error': 'Erro interno'}), 500
```

**Impact:**  
- Silent failures mask underlying bugs
- No audit trail for debugging
- Potential security issue (could leak stack traces)
- Difficult to diagnose production issues

**Recommendation:**  
Implement structured error handling:

```python
import logging

logger = logging.getLogger(__name__)

try:
    db.session.commit()
except IntegrityError as e:
    logger.error(f"Integrity error: {str(e)}")
    db.session.rollback()
    return jsonify({'error': 'Duplicate entry'}), 409
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
```

---

### M3 — Missing Centralized Input Validation
**Severity:** MEDIUM  
**Pattern:** M2 (Missing Input Validation)  
**Files:** All route handlers

**Description:**  
Validation logic scattered across route handlers without schema framework:
- Email validation regex duplicated (user_routes.py:61, 106)
- Title length validation duplicated (task_routes.py:96-100, 167-170)
- Status/priority validation repeated throughout

**Impact:**  
- Inconsistent validation behavior
- Hard to maintain and update rules
- Error-prone when adding new endpoints

**Recommendation:**  
Use Marshmallow (already in requirements.txt) to centralize schemas:

```python
# In schemas.py
from marshmallow import Schema, fields, validate

class TaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str()
    status = fields.Str(validate=validate.OneOf(['pending', 'in_progress', 'done', 'cancelled']))
    priority = fields.Int(validate=validate.Range(min=1, max=5))

# In routes
task_schema = TaskSchema()

@task_bp.route('/tasks', methods=['POST'])
def create_task():
    errors = task_schema.validate(request.get_json())
    if errors:
        return jsonify(errors), 400
    validated_data = task_schema.load(request.get_json())
    # ... create task
```

---

## LOW Issues

### L1 — Magic Numbers and Strings
**Severity:** LOW  
**Pattern:** L1 (Magic Numbers)  
**Files:**
- `routes/report_routes.py`, lines 24-28 (p1, p2, p3, p4, p5 priority counts)
- `routes/report_routes.py`, line 45 (hardcoded '7' days)

**Description:**  
Business constants hardcoded throughout code:
```python
p1 = Task.query.filter_by(priority=1).count()  # What does 1 mean?
seven_days_ago = datetime.utcnow() - timedelta(days=7)  # Magic number
```

**Impact:**  
- Reduced code readability
- Difficult to update constants globally
- Easy to introduce inconsistencies

**Recommendation:**  
Extract to configuration constants:

```python
# In config.py or constants.py
PRIORITY_LEVELS = {
    1: 'critical',
    2: 'high',
    3: 'medium',
    4: 'low',
    5: 'minimal'
}

REPORT_LOOKBACK_DAYS = 7

# Usage
recent_tasks = Task.query.filter(
    Task.created_at >= datetime.utcnow() - timedelta(days=REPORT_LOOKBACK_DAYS)
).count()
```

---

### L2 — Poor Variable Naming
**Severity:** LOW  
**Pattern:** L2 (Poor Naming)  
**Files:**
- `routes/report_routes.py`, lines 24-28 (p1, p2, p3, p4, p5)
- `routes/task_routes.py`, lines 16-59 (t, u, cat)
- `routes/report_routes.py`, lines 111-116 (done, pending, in_progress, cancelled — repetitive)

**Description:**  
Single-letter and abbreviated variable names reduce code clarity:
```python
for t in tasks:  # What is 't'? Should be 'task'
    if t.user_id:
        user = User.query.get(t.user_id)
        task_data['user_name'] = user.name
```

**Impact:**  
- Reduced readability
- Harder to understand code intent
- More prone to maintenance errors

**Recommendation:**  
Use descriptive names:
```python
for task in tasks:
    if task.user_id:
        assignee = User.query.get(task.user_id)
        task_data['user_name'] = assignee.name

# For priority counts
priority_critical_count = Task.query.filter_by(priority=1).count()
priority_high_count = Task.query.filter_by(priority=2).count()
# ... or use a loop
```

---

### L3 — Unused Imports (Dead Code)
**Severity:** LOW  
**Pattern:** L3 (Dead Code)  
**Files:**
- `app.py`, line 7 (os, sys, json, datetime unused)
- `routes/task_routes.py`, line 7 (json, os, sys, time unused)
- `routes/user_routes.py`, line 6 (json unused)
- `routes/report_routes.py`, line 8 (json unused)
- `utils/helpers.py`, lines 3-6 (os, json, sys, math, hashlib unused)

**Description:**  
Imports present but never used in the module, cluttering the code.

**Impact:**  
- Reduced code clarity
- Confusion about dependencies
- Potential security concern if unused libraries have vulnerabilities

**Recommendation:**  
Remove all unused imports using a linter:
```bash
# Install flake8
pip install flake8

# Identify unused imports
flake8 --select=F401 .

# Auto-fix (requires autoflake)
autoflake --in-place --remove-all-unused-imports .
```

---

## Summary Table

| Severity | Count | Pattern | Primary Issue |
|----------|-------|---------|----------------|
| CRITICAL | 2 | C2, Security | Hardcoded credentials, weak password hashing |
| HIGH | 2 | H1, H5 | Fat controllers, missing abstraction |
| MEDIUM | 3 | M1, M2, M3 | N+1 queries, validation, error handling |
| LOW | 6 | L1, L2, L3 | Magic numbers, naming, dead code |
| **TOTAL** | **13** | — | — |

---

## Recommended Refactoring Priority

1. **Phase 1 (Critical → Security):**
   - Move hardcoded secrets to `.env`
   - Replace MD5 with bcrypt password hashing
   - Add `.gitignore` entry for `.env`

2. **Phase 2 (High → Architecture):**
   - Extract business logic into service classes
   - Introduce repository pattern for data access
   - Implement dependency injection for services

3. **Phase 3 (Medium → Quality):**
   - Implement eager loading to eliminate N+1 queries
   - Centralize validation using Marshmallow schemas
   - Add structured error handling and logging

4. **Phase 4 (Low → Readability):**
   - Extract magic numbers to configuration
   - Rename variables for clarity
   - Remove unused imports

---

## Testing Recommendations

After refactoring:
- ✓ Unit tests for service layer
- ✓ Integration tests with real database
- ✓ API tests for all endpoints
- ✓ Performance tests to verify N+1 fix
- ✓ Security tests for credential isolation

---

*End of Audit Report*

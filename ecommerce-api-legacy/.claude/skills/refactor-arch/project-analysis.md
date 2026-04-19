# Project Analysis Heuristics

Heuristics for detecting language, framework, database, and architecture during Phase 1.

---

## Language Detection

| Signal | Language |
|--------|----------|
| `*.py` files + `import flask` / `import django` / `import fastapi` | Python |
| `package.json` + `require('express')` / `import express` | Node.js/JavaScript |
| `package.json` + `tsconfig.json` | TypeScript |
| `*.php` + `artisan` or `composer.json` | PHP |
| `Gemfile` + `*.rb` | Ruby |
| `pom.xml` or `build.gradle` + `*.java` | Java |
| `go.mod` + `*.go` | Go |
| `*.cs` + `*.csproj` | C# (.NET) |

---

## Framework Detection

### Python
| Signal | Framework |
|--------|-----------|
| `from flask import Flask` or `Flask(__name__)` | Flask |
| `from django.db import models` or `manage.py` | Django |
| `from fastapi import FastAPI` | FastAPI |

### Node.js
| Signal | Framework |
|--------|-----------|
| `require('express')` / `import express` | Express.js |
| `@nestjs/core` in package.json | NestJS |
| `next` in package.json | Next.js |

### PHP / Ruby / Java
| Signal | Framework |
|--------|-----------|
| `artisan`, `App\Http\Controllers` | Laravel |
| `config/routes.rb`, `ApplicationController` | Rails |
| `@SpringBootApplication` | Spring Boot |

---

## Version Detection

- Python: `requirements.txt`, `Pipfile`, `pyproject.toml` — look for version pins
- Node.js: `package.json` → `dependencies` and `devDependencies` fields
- PHP: `composer.json` → `require` section
- Ruby: `Gemfile` → gem declarations

---

## Database Detection

| Signal | Database |
|--------|----------|
| `sqlite3.connect(...)` or `*.db` / `*.sqlite3` file | SQLite |
| `psycopg2`, `DATABASE_URL=postgresql://` | PostgreSQL |
| `pymysql`, `mysql-connector`, `mysql://` in URL | MySQL |
| `MongoClient`, `mongoose` | MongoDB |
| `redis`, `Redis()` | Redis |
| `sqlalchemy` with any backend | SQLAlchemy ORM (detect underlying DB from URL) |

---

## Architecture Pattern Detection

| Signal | Architecture |
|--------|-------------|
| All routes, DB calls, and logic in a single entry file | Flat / Monolith (no layers) |
| Folders: `models/`, `controllers/`, `views/` or `routes/` | MVC (partial or full) |
| Folders: `services/`, `repositories/`, `domain/` | Layered / Clean Architecture |
| Multiple `app/` sub-apps or bounded context folders | Modular Monolith |
| Separate repos or `docker-compose` with 3+ services | Microservices |

---

## Domain Area Detection

Infer business domains from:
- Route prefixes: `/products`, `/users`, `/orders`, `/payments`
- Model/entity names in DB schema or ORM definitions
- Controller or service file names
- Table names found in SQL statements

---

## Source File Count and LOC

```bash
# Count source files by extension
find . -name "*.py" | wc -l          # Python
find . -name "*.js" | wc -l          # JS
find . -name "*.ts" | wc -l          # TS

# Approximate lines of code (excluding blank lines and comments)
wc -l $(find . -name "*.py" ! -path "./.venv/*" ! -path "./node_modules/*")
```

Report the total as "~N lines of code" rounded to nearest 50.

---

## Phase 1 Output Format

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <lang> <version if detected>
Framework:     <framework> <version if detected>
Dependencies:  <comma-separated key deps>
Domain:        <business domain description>
Architecture:  <pattern> — <brief description>
Source files:  <N> files analyzed
DB tables:     <table/collection list>
================================
```

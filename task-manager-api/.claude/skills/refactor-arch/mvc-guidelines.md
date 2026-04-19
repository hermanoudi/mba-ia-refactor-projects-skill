# MVC Architecture Guidelines

## Core Principle

Each layer has one responsibility. Nothing leaks between layers.

```
Request → Routes/Views → Controller → Model → DB
                ↑             ↓
             Response    Business Logic
```

## Layer Rules

### Models
**Responsibility:** Data access, schema definition, domain logic.

Rules:
- Own all database queries and ORM interactions
- May contain domain validation (e.g., field constraints)
- Must NOT construct HTTP responses
- Must NOT import routing or controller modules
- One model file per domain entity (User, Product, Order…)

Examples by technology:
- Python/Flask: SQLAlchemy models or raw query functions in `models/<entity>_model.py`
- Node.js/Express: Mongoose schemas or Sequelize models in `models/<entity>.model.js`
- PHP/Laravel: Eloquent model class in `app/Models/<Entity>.php`
- Ruby/Rails: ActiveRecord model in `app/models/<entity>.rb`

### Controllers
**Responsibility:** Orchestrate business logic, call models, return data.

Rules:
- Receive validated input from the route layer
- Call one or more model methods
- Apply business rules and transformations
- Return plain data (dict, object, DTO) — NOT HTTP response objects
- Must NOT write SQL or ORM queries
- Must NOT import route definitions

Examples by technology:
- Python/Flask: Plain functions in `controllers/<domain>_controller.py` returning dicts
- Node.js/Express: Async functions in `controllers/<domain>.controller.js`
- PHP/Laravel: Controller class in `app/Http/Controllers/<Domain>Controller.php`

### Views / Routes
**Responsibility:** HTTP boundary — validate input, call controller, serialize response.

Rules:
- Define URL patterns and HTTP methods
- Validate and sanitize request input (query params, body, headers)
- Call the appropriate controller function
- Serialize controller return value to HTTP response (JSON, HTML, etc.)
- Must NOT contain business logic or direct DB access
- One route file per domain or feature area

Examples by technology:
- Python/Flask: Blueprint in `views/<domain>_routes.py`
- Node.js/Express: Router in `routes/<domain>.routes.js`
- PHP/Laravel: `routes/api.php` + resource controllers
- Ruby/Rails: `config/routes.rb` + view templates

### Config / Settings
**Responsibility:** Environment-specific configuration.

Rules:
- All secrets loaded from environment variables (never hardcoded)
- Database connection strings, API keys, feature flags live here
- Application-wide constants go here (not scattered as magic numbers)

### Middlewares
**Responsibility:** Cross-cutting concerns applied to many routes.

Use for:
- Authentication / authorization
- Request logging
- Error handling (centralized)
- CORS, rate limiting, compression

Must NOT contain business logic for a specific domain.

### App / Entry Point
**Responsibility:** Composition root — wire everything together.

Rules:
- Import and register routes/blueprints
- Initialize middleware
- Start server
- Must NOT contain business logic

## Target Directory Structure

```
src/                          # or app/ depending on framework
├── config/
│   └── settings.<ext>
├── models/
│   ├── <entity1>_model.<ext>
│   └── <entity2>_model.<ext>
├── controllers/
│   ├── <domain1>_controller.<ext>
│   └── <domain2>_controller.<ext>
├── views/                    # or routes/
│   ├── <domain1>_routes.<ext>
│   └── <domain2>_routes.<ext>
├── middlewares/
│   └── error_handler.<ext>
└── app.<ext>                 # composition root
```

Adapt directory names to framework conventions (e.g., `Http/Controllers` for Laravel, `app/controllers` for Rails).

# 🗺️ Hive GitHub Project Roadmap

> **Project**: Hive — The Open-Source Campus Platform  
> **Goal**: Transform the Code-JAM Flask prototype into a production-ready, self-hostable platform (v1.0).

---

## 🎯 Milestone: v0.2 - Foundation & Technical Debt Eradication
**Goal**: Establish a safe development environment, remove hardcoded PII, and fix critical security/bug issues before major refactoring begins.

### Issue #1: Remove all real student PII from seed script
- **Description**: The `init_db.py` file contains 1,154 lines of hardcoded data, including real student names and emails from Sai University. This is a severe privacy violation for an open-source repo. We need to purge this and replace it with generic, fictional demo data.
- **Acceptance Criteria**: 
  - `init_db.py` contains zero real names, emails, or institution-specific codes (SCDS/SOAI).
  - A new `fixtures/demo.json` (or similar) generates John Doe/Jane Doe accounts.
  - The database seeds successfully with fake data.
- **Estimated Difficulty**: 🟩 Easy (but tedious)
- **Dependencies**: None
- **Priority**: 🔴 Critical / P0

### Issue #2: Implement Alembic database migrations
- **Description**: Currently, the app uses `db.create_all()` and `drop_all()`. We cannot evolve the database schema without destroying data. Integrate Flask-Migrate (Alembic) to handle schema versioning.
- **Acceptance Criteria**: 
  - `flask db init`, `migrate`, and `upgrade` commands work.
  - Initial migration script is generated for the current schema.
  - `run.py` no longer calls `db.drop_all()`.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: None
- **Priority**: 🔴 Critical / P0

### Issue #3: Fix Role String Bugs in Messaging
- **Description**: `messages.py` checks for `'teacher'` and `'assistant'`, but `VALID_ROLES` only contains `'professor'` and `'assistant_professor'`. This causes messaging filters to silently fail.
- **Acceptance Criteria**: 
  - `messages.py` uses `VALID_ROLES` constants consistently.
  - Users with 'professor' and 'assistant_professor' roles can send and receive messages properly.
- **Estimated Difficulty**: 🟩 Easy
- **Dependencies**: None
- **Priority**: 🟠 High / P1

### Issue #4: Implement global CSRF Protection
- **Description**: The app lacks Cross-Site Request Forgery (CSRF) protection (acknowledged in `messages.py`). Add Flask-WTF and ensure all POST requests are protected.
- **Acceptance Criteria**: 
  - Flask-WTF `CSRFProtect` is initialized globally.
  - All forms include `{{ csrf_token() }}`.
  - AJAX POST requests include the CSRF token in headers.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: None
- **Priority**: 🔴 Critical / P0

### Issue #5: Setup testing infrastructure (pytest)
- **Description**: The project has zero tests. We need a basic testing harness so we can verify our upcoming refactors don't break core functionality.
- **Acceptance Criteria**: 
  - `pytest` is configured in `pyproject.toml`.
  - `conftest.py` provides `app`, `client`, and `db` fixtures.
  - One basic smoke test (e.g., test login page loads) is written and passes.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: None
- **Priority**: 🟠 High / P1

---

## 🎯 Milestone: v0.3 - Core Architecture Extraction
**Goal**: Pull out the foundational layers (Authentication, Multi-tenancy, Settings) into independent, isolated core modules.

### Issue #6: Build the SiteSettings KV Store
- **Description**: Replace hardcoded values (currency, timezone, day ranges) with a database-backed `SiteSetting` key-value model to allow GUI-based configuration.
- **Acceptance Criteria**: 
  - `SiteSetting` model created.
  - Helper functions `get_setting()` and `set_setting()` implemented.
  - Currency symbol (₹) and low CGPA threshold (1.5) replaced with settings lookups.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: #2 (Alembic)
- **Priority**: 🟠 High / P1

### Issue #7: Extract Authentication Core Module
- **Description**: Move all auth logic (`auth.py`, login, session handling, password hashing) into a standalone `hive/core/auth/` module.
- **Acceptance Criteria**: 
  - `auth` blueprint registered successfully from the new location.
  - Login/logout flows work exactly as before.
  - In-memory rate limiting replaced with a robust solution (e.g., Flask-Limiter).
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: #5 (pytest)
- **Priority**: 🟠 High / P1

### Issue #8: Extract Tenant (Institution) Core Module
- **Description**: Move `school_scoped` middleware and tenant resolution into `hive/core/tenant/`. Expand the `School` model into `Institution`, `Department`, and `AcademicYear`.
- **Acceptance Criteria**: 
  - `Institution` and `AcademicYear` models exist.
  - `@tenant_scoped` middleware properly injects `g.institution_id`.
  - Old `School` references migrated.
- **Estimated Difficulty**: 🟧 Hard
- **Dependencies**: #2 (Alembic)
- **Priority**: 🟠 High / P1

### Issue #9: Migrate to UUID Primary Keys
- **Description**: Integer IDs allow enumeration attacks and make multi-DB scaling difficult. Convert all primary keys from integers to UUIDs.
- **Acceptance Criteria**: 
  - All DB models use `UUID(as_uuid=True)` for PKs and FKs.
  - URLs reflect UUIDs (e.g., `/courses/123e4567-e89b...`).
  - Alembic migration successfully alters the schema.
- **Estimated Difficulty**: 🟧 Hard
- **Dependencies**: #2, #8
- **Priority**: 🟡 Medium / P2

---

## 🎯 Milestone: v0.4 - Module Decomposition (Breaking the Monolith)
**Goal**: Break the 1,185-line `dashboard.py` God Blueprint and the 650-line `models.py` into feature-specific, independent modules.

### Issue #10: Decompose models.py into domains
- **Description**: Break the single `models.py` file into feature-specific model files (`academics/models.py`, `assessment/models.py`, `fees/models.py`, etc.).
- **Acceptance Criteria**: 
  - `app/models.py` no longer exists.
  - SQLAlchemy models are loaded from their respective module directories.
  - Alembic still detects and manages all models correctly.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: #8
- **Priority**: 🟠 High / P1

### Issue #11: Split dashboard.py into Feature Routes
- **Description**: Disassemble the massive `dashboard.py` blueprint. Move Timetable routes to the Timetable module, Analytics to the Analytics module, etc.
- **Acceptance Criteria**: 
  - `dashboard.py` is removed.
  - At least 5 new blueprints are registered (`academics`, `timetable`, `assessment`, `analytics`, `classroom`).
  - Navigation links in the UI are updated to point to the new endpoints.
- **Estimated Difficulty**: 🟥 Very Hard
- **Dependencies**: #10
- **Priority**: 🟠 High / P1

### Issue #12: Extract Business Logic into Service Layers
- **Description**: Move complex logic (e.g., finding common free slots, calculating early warning flags) out of route handlers and into `services.py` files.
- **Acceptance Criteria**: 
  - Route handlers only handle HTTP (request parsing, rendering).
  - Business logic resides in `services.py`.
  - Service functions have unit tests.
- **Estimated Difficulty**: 🟧 Hard
- **Dependencies**: #11
- **Priority**: 🟡 Medium / P2

### Issue #13: Reorganize Templates Directory
- **Description**: Move templates from the global `templates/` folder into their respective module folders (e.g., `modules/timetable/templates/timetable/`).
- **Acceptance Criteria**: 
  - Global `templates/` only contains `base.html` and core layouts.
  - Blueprints successfully load templates from their local folders.
- **Estimated Difficulty**: 🟩 Easy
- **Dependencies**: #11
- **Priority**: 🟡 Medium / P2

---

## 🎯 Milestone: v0.5 - Deployment & Setup Tools
**Goal**: Make Hive easily deployable for any college administrator without requiring them to write code or manual SQL scripts.

### Issue #14: Build CSV Import Engine
- **Description**: Create a robust engine to import Students, Faculty, Courses, and Timetables via CSV/Excel, with validation and rollback capabilities.
- **Acceptance Criteria**: 
  - Admin UI for uploading CSVs.
  - Preview screen showing column mapping and validation errors.
  - Successful bulk insertion of valid rows.
- **Estimated Difficulty**: 🟧 Hard
- **Dependencies**: #10
- **Priority**: 🟠 High / P1

### Issue #15: Interactive Setup Wizard (First-Run Experience)
- **Description**: Create a `/setup` flow that runs when the database has no admin users. It should guide the user through institution naming, admin account creation, and module selection.
- **Acceptance Criteria**: 
  - Visiting the root URL redirects to `/setup` if unconfigured.
  - Wizard completes 4 steps (DB config, Admin Account, Institution Details, Theme).
  - Upon completion, `setup_complete` flag is set to True.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: #6 (Settings)
- **Priority**: 🟠 High / P1

### Issue #16: Dockerize the Application
- **Description**: Create a production-ready `Dockerfile` and `docker-compose.yml` that spins up Hive, PostgreSQL, Redis, and Nginx.
- **Acceptance Criteria**: 
  - `docker compose up -d` results in a fully working Hive instance.
  - Data persists across container restarts via volumes.
  - Environment variables correctly pass into the containers.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: None
- **Priority**: 🟡 Medium / P2

### Issue #17: Create CLI Management Commands
- **Description**: Use `Click` to build CLI tools for server admins (`hive backup`, `hive create-admin`, `hive import`).
- **Acceptance Criteria**: 
  - `flask cli` or custom `hive` command runs successfully from the terminal.
  - Can create a superadmin user via CLI.
- **Estimated Difficulty**: 🟩 Easy
- **Dependencies**: None
- **Priority**: 🟡 Medium / P2

---

## 🎯 Milestone: v1.0 - Extensibility & Public API (The WordPress Experience)
**Goal**: Finalize the platform architecture so third-party developers can build themes, plugins, and mobile apps.

### Issue #18: Implement Plugin Registry and Hooks
- **Description**: Build the engine that discovers `plugin.json` manifests, registers them, and allows them to hook into core events (using `blinker`).
- **Acceptance Criteria**: 
  - A dummy plugin can be placed in the `plugins/` folder and activated via UI.
  - Plugin can successfully hook into `user_logged_in` signal.
  - Admin panel shows installed plugins.
- **Estimated Difficulty**: 🟧 Hard
- **Dependencies**: #11, #12
- **Priority**: 🟡 Medium / P2

### Issue #19: Implement Theme Engine (CSS Variables)
- **Description**: Create a theme loader that cascades templates and CSS variables, allowing institutions to reskin Hive completely without modifying core files.
- **Acceptance Criteria**: 
  - Admin can switch between "Default Light" and "Default Dark" from settings.
  - Admin can override primary colors, which dynamically updates CSS variables in `base.html`.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: #6
- **Priority**: 🟡 Medium / P2

### Issue #20: Build REST API v1
- **Description**: Expose core entities (Courses, Timetables, Users) via versioned REST endpoints authenticated with JWTs.
- **Acceptance Criteria**: 
  - `flask-smorest` or `flask-restx` is integrated.
  - JWT authentication is working.
  - GET `/api/v1/timetable/me` returns the current user's timetable as JSON.
  - OpenAPI/Swagger UI is auto-generated at `/api/docs`.
- **Estimated Difficulty**: 🟧 Hard
- **Dependencies**: #7 (Auth), #10 (Models)
- **Priority**: 🟡 Medium / P2

### Issue #21: Launch Documentation Site & Beta Release
- **Description**: Write the official setup guide, plugin development tutorial, and theme development guide, marking the v1.0 Release Candidate.
- **Acceptance Criteria**: 
  - `docs/` folder contains Markdown files for Setup, Architecture, and Extension.
  - README is updated with Docker quickstart instructions.
  - v1.0 tag is cut on GitHub.
- **Estimated Difficulty**: 🟨 Medium
- **Dependencies**: #15, #16, #18, #19, #20
- **Priority**: 🟠 High / P1

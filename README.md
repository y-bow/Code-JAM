# Hive — Open-Source Campus Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask: 3.0.2](https://img.shields.io/badge/Flask-3.0.2-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://docker.com)

A modern, self-hostable campus platform for colleges and universities. Hive provides multi-tenant data isolation, role-based access control, a plugin system, REST API, and theming — all in a clean, modular Flask application.

---

## Quick Start with Docker

```bash
git clone https://github.com/y-bow/Code-JAM.git
cd Code-JAM
cp .env.example .env
docker compose up -d
docker compose exec web flask db upgrade
docker compose exec web flask hive create-admin \
    --email admin@example.com \
    --password changeme \
    --name "Admin User"
```

Open **http://localhost:8080** and complete the Setup Wizard.

> See [docs/Setup Guide.md](docs/Setup%20Guide.md) for manual installation and production deployment.

---

## Key Features

| Feature               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Multi-tenancy**     | Full data isolation between schools, departments, and sections               |
| **RBAC**              | Distinct dashboards for Admins, Deans, Professors, Assistants, and Students |
| **Course Management** | Enrollment, assignments, quizzes, grades, and resource management           |
| **Timetable System**  | Dynamic section-specific schedules with color-coded categories              |
| **Analytics**         | Real-time insights, teacher ratings, early warning for at-risk students     |
| **Messaging**         | In-app messaging with read receipts and announcements                       |
| **Fees & Payments**   | Fee structure management and payment tracking                               |
| **Clubs & Events**    | Student clubs, external events, class representative nominations            |
| **Internships**       | Internship opportunity listings and applications                            |
| **Lost & Found**      | Lost item reporting and gallery                                             |
| **CSV Import**        | Bulk import students, faculty, courses, and timetable via CSV/Excel         |
| **Plugin System**     | Extend functionality via `plugin.json` manifests and blinker event hooks    |
| **Theme Engine**      | Customize colors and light/dark mode from the admin panel                   |
| **REST API v1**       | JWT-authenticated API with auto-generated Swagger docs at `/api/docs/`      |
| **CLI Tools**         | `flask hive create-admin`, `flask hive backup`, `flask hive import`         |

---

## Project Structure

```text
.
├── app/                    # Flask application package
│   ├── api/                # REST API v1 (flask-smorest, JWT auth)
│   ├── core/               # Core modules (auth, tenant, plugins)
│   ├── models/             # Domain models (15 modules, re-exported)
│   ├── routes/             # Feature blueprints (12 modules)
│   ├── services/           # Business logic layer
│   ├── cli.py              # Flask CLI commands
│   ├── events.py           # blinker signal definitions
│   └── __init__.py         # Application factory
├── plugins/                # Plugin packages (hello_world sample)
├── static/                 # CSS, JS, images
├── templates/              # Jinja2 base layout
├── docs/                   # Architecture, Setup, Extension guides
├── migrations/             # Alembic database migrations
├── tests/                  # pytest test suite (21 tests)
├── nginx/                  # Nginx reverse proxy config (Docker)
├── Dockerfile              # Production container image
├── docker-compose.yml      # PostgreSQL + Redis + Nginx + Hive
├── .env.example            # Environment variable template
└── requirements.txt        # Python dependencies
```

---

## Documentation

| Guide                    | Description                                  |
|--------------------------|----------------------------------------------|
| [Setup Guide](docs/Setup%20Guide.md) | Installation, configuration, deployment     |
| [Architecture](docs/Hive%20Architectural%20Analysis.md) | System design, modules, data flow |
| [Plugin Development](docs/Plugin%20Development.md) | Creating and distributing plugins |
| [Theme Development](docs/Theme%20Development.md) | Customizing appearance        |
| [GitHub Roadmap](docs/GitHub%20Roadmap.md) | Project roadmap and milestones    |
| [PRD](docs/PRD.md)         | Product requirements document                 |

---

## API Endpoints

| Method | Endpoint                    | Description                |
|--------|-----------------------------|----------------------------|
| POST   | `/api/v1/auth/login`        | Authenticate, get JWT token|
| GET    | `/api/v1/auth/me`           | Current user info          |
| GET    | `/api/v1/timetable/me`      | Current user's timetable   |

Swagger UI: `/api/docs/`

---

## Default Credentials

After running the setup wizard or seeding the database:

| Role             | Email                           | Password     |
|------------------|---------------------------------|--------------|
| Superadmin       | (set during setup/CLI)          | (user-set)   |
| Admin            | (set during setup/CLI)          | (user-set)   |

> Create an admin user with `flask hive create-admin --email admin@example.com --password <secure> --name "Admin"`

---

## License

MIT License — see [LICENSE](LICENSE).

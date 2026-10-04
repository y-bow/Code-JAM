# Hive — Open-Source Campus Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://docker.com)

A self-hostable campus platform any college can deploy. Hive provides multi-tenant data isolation, role-based access, a plugin system, REST API, and custom theming — no source code changes required.

---

## Quick Start

### Docker (production)

```bash
git clone https://github.com/y-bow/Code-JAM.git
cd Code-JAM
cp .env.example .env
# Edit .env — set SECRET_KEY and JWT_SECRET_KEY to secure values
docker compose up -d
```

Open **http://localhost:80** and complete the Setup Wizard to create your admin account and institution.

### Manual (development)

```bash
git clone https://github.com/y-bow/Code-JAM.git
cd Code-JAM
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open **http://localhost:5000** and complete the Setup Wizard.

> For detailed installation options, see [docs/Setup Guide.md](docs/Setup%20Guide.md).

---

## Features

| Area | What Hive provides |
|------|-------------------|
| **Multi-tenancy** | Full data isolation between schools, departments, sections |
| **Role-based access** | Separate dashboards for Admin, Dean, Professor, Assistant, Student, Class Rep |
| **Course management** | Enrollment, assignments, quizzes, grades, resources, meet links |
| **Timetable** | Section-specific schedules with color-coded categories and free-slot detection |
| **Analytics** | School stats, teacher ratings, early warning for at-risk students |
| **Messaging** | In-app messaging with read receipts and announcements |
| **Fees** | Fee structure, payment tracking, printable receipts |
| **Clubs & events** | Student clubs, event listings, class representative nominations |
| **Internships** | Opportunity listings and student applications |
| **Lost & found** | Item reporting with gallery |
| **CSV import** | Bulk-import students, faculty, courses, timetable via CSV or Excel |
| **Plugin system** | Extend Hive via `plugin.json` manifests and blinker event hooks |
| **Theme engine** | Customize colors and light/dark mode from the admin panel |
| **REST API v1** | JWT-authenticated API with Swagger docs at `/api/docs/` |
| **CLI tools** | `flask hive create-admin`, `flask hive backup`, `flask hive import` |

---

## Admin Settings

Every institution-specific value is configurable from **Admin → Settings**:

- Institution name, department, address, finance email
- Currency symbol (for fee receipts and payments)
- Early warning thresholds (CGPA and attendance)
- CSV import default password
- Theme mode and primary color

No source code changes needed to adapt Hive to your college.

---

## Project Structure

```
├── app/                      Flask application
│   ├── api/                  REST API v1 (flask-smorest, JWT)
│   ├── core/                 Core modules (auth, tenant, plugins)
│   ├── models/               SQLAlchemy models (15 modules)
│   ├── routes/               Feature blueprints (12 routes)
│   ├── services/             Business logic layer
│   ├── cli.py                Flask CLI commands
│   ├── events.py             blinker signal definitions
│   └── __init__.py           Application factory
├── plugins/                  Plugin packages (hello_world sample)
├── docs/                     Architecture, Setup, Extension guides
├── migrations/               Alembic database migrations
├── tests/                    pytest suite (21 tests)
├── nginx/                    Nginx configuration (Docker)
├── Dockerfile                Production container image
├── docker-compose.yml        PostgreSQL + Redis + Nginx + Hive
├── .env.example              Environment variable template
└── requirements.txt          Python dependencies
```

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Setup Guide](docs/Setup%20Guide.md) | Installation, configuration, production deployment |
| [Architecture](docs/Hive%20Architectural%20Analysis.md) | System design, modules, data flow |
| [Plugin Development](docs/Plugin%20Development.md) | Creating and distributing plugins |
| [Theme Development](docs/Theme%20Development.md) | Customizing appearance |
| [GitHub Roadmap](docs/GitHub%20Roadmap.md) | Project roadmap and milestones |
| [PRD](docs/PRD.md) | Product requirements |

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate, get JWT token |
| GET | `/api/v1/auth/me` | Current user info |
| GET | `/api/v1/timetable/me` | Current user's timetable |

Swagger UI: `/api/docs/`

---

## Default Credentials

After completing the Setup Wizard, the admin account you created is the only user. Add users via CSV import or the admin panel.

Development seeding (`python run.py --reseed` with `FLASK_ENV=development`) creates demo accounts:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@demo.edu` | `hive@1234` |
| Dean | `dean@soe.demo.edu` | `hive@1234` |
| Professor | `professor@soe.demo.edu` | `hive@1234` |

---

## License

MIT — see [LICENSE](LICENSE).

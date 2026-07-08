# Hive Setup Guide

> **Version**: v1.0 — Release Candidate

This guide covers all methods for deploying and running Hive, from local development to production.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start (Docker)](#2-quick-start-docker)
3. [Manual Installation](#3-manual-installation)
4. [Configuration](#4-configuration)
5. [Database Setup](#5-database-setup)
6. [Running the Application](#6-running-the-application)
7. [Setup Wizard](#7-setup-wizard)
8. [CLI Commands](#8-cli-commands)
9. [Production Deployment](#9-production-deployment)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

- **Docker** and **Docker Compose** (recommended) **or**
- **Python 3.10+** and **pip**
- **PostgreSQL 16+** (for production) or SQLite (for development)
- **Redis 7+** (for rate limiting in production)

---

## 2. Quick Start (Docker)

The fastest way to run Hive:

```bash
# Clone the repository
git clone https://github.com/y-bow/Code-JAM.git
cd Code-JAM

# Copy environment configuration
cp .env.example .env
# Edit .env with your own SECRET_KEY

# Start all services
docker compose up -d

# Run database migrations
docker compose exec web flask db upgrade

# Create your first admin user
docker compose exec web flask hive create-admin \
    --email admin@example.com \
    --password changeme \
    --name "Admin User"

# Open http://localhost:8080 and complete the Setup Wizard
```

### Docker Services

| Service     | Port  | Description              |
|-------------|-------|--------------------------|
| **Hive**    | 5000  | Flask application        |
| **Nginx**   | 8080  | Reverse proxy (front-end)|
| **PostgreSQL** | 5432 | Database               |
| **Redis**   | 6379  | Cache / rate limiting    |

---

## 3. Manual Installation

### 3.1 Clone and Prepare

```bash
git clone https://github.com/y-bow/Code-JAM.git
cd Code-JAM

python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3.2 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:

| Variable       | Description                          | Default                          |
|----------------|--------------------------------------|----------------------------------|
| `SECRET_KEY`   | Flask secret key (change in prod)    | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | Database connection string           | `sqlite:///instance/app.db`      |
| `REDIS_URL`    | Redis connection (production only)   | `redis://localhost:6379/0`       |
| `JWT_SECRET_KEY` | JWT signing key (defaults to SECRET_KEY) | same as SECRET_KEY          |

> **PostgreSQL connection string**: `postgresql://user:password@host:5432/dbname`

---

## 4. Configuration

All application settings are managed through Hive's built-in **Site Settings** admin panel (`/admin/settings`) after first login.

### Configurable Settings

| Setting Key              | Description                  | Default  |
|--------------------------|------------------------------|----------|
| `theme.active`           | Default theme (light/dark)   | `light`  |
| `theme.primary_color`    | Brand primary color (hex)    | `#2563eb`|

Additional settings are created dynamically as features require them.

---

## 5. Database Setup

### Fresh Database

```bash
# Apply all migrations
flask db upgrade

# Seed demo data (optional)
flask hive import --type students --file data/students.csv
flask hive import --type faculty --file data/faculty.csv
```

### Creating an Admin User

```bash
# Create a superadmin user
flask hive create-admin \
    --email admin@mycollege.edu \
    --password <secure-password> \
    --name "College Admin"
```

---

## 6. Running the Application

### Development

```bash
flask run
# or
python run.py
```

The app starts at `http://localhost:5000`.

### Production (Manual)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

---

## 7. Setup Wizard

On first run (no admin users, no schools configured), Hive automatically redirects all pages to the **Setup Wizard** at `/setup`.

The wizard has 4 steps:

1. **Admin Account** — Create the initial superadmin user
2. **Institution** — Configure your institution name and details
3. **Theme** — Select default theme mode and primary color
4. **Complete** — Summary and confirmation

After completion, the setup flag is set and the wizard will not appear again.

---

## 8. CLI Commands

Hive provides a `flask hive` CLI group with helpful management commands:

### `flask hive create-admin`

Create admin or superadmin users:

```bash
flask hive create-admin \
    --email admin@example.com \
    --password secret123 \
    --name "Admin" \
    --role admin
# --role defaults to superadmin if omitted
```

### `flask hive backup`

Backup the database (supports both SQLite and PostgreSQL):

```bash
flask hive backup
# Creates instance/backups/hive_backup_<timestamp>.sql or .dump
```

### `flask hive import`

Import data from CSV files:

```bash
flask hive import \
    --type students \           # students | faculty | courses | timetable | enrollments
    --file data/students.csv \
    --dry-run                   # Preview without committing
```

---

## 9. Production Deployment

### System Requirements

- **Python 3.10+** (tested on 3.14)
- **PostgreSQL 16+** (SQLite not recommended for production)
- **Redis 7+** (for rate limiting)
- **Nginx** (reverse proxy, optional but recommended)

### Environment Variables

Set these in production (not `.env` file — use your platform's secrets):

```bash
export SECRET_KEY=<random-64-char-string>
export DATABASE_URL=postgresql://hive:password@db:5432/hive
export REDIS_URL=redis://redis:6379/0
export JWT_SECRET_KEY=<different-random-string>
```

### Docker Deployment

For production Docker, use the provided `docker-compose.yml`:

```bash
docker compose -f docker-compose.yml up -d
```

The Nginx reverse proxy serves Hive on port **8080** with gunicorn handling Python requests behind the scenes.

---

## 10. Troubleshooting

| Problem                         | Solution                                              |
|---------------------------------|-------------------------------------------------------|
| `flask: command not found`      | Activate your virtual environment first               |
| Database migration fails        | Run `flask db upgrade` to apply pending migrations    |
| Setup Wizard loops              | Ensure at least one admin user and school exist       |
| 500 error on first visit        | Run `flask db upgrade` to create tables               |
| CSRF token missing              | Refresh the page and try again; API users skip CSRF   |
| JWT token expired               | Tokens last 24 hours; re-login to get a new one       |

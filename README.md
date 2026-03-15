# LMS Prototype - Code-JAM

A university Learning Management System (LMS) prototype built for FOSS Hack 2026. This platform features multi-tenant architecture with role-based access control for Chancellors, Teachers, and Students.

## Features
- **Multi-tenancy**: Data isolated per school.
- **Role-based Access**: Custom dashboards and permissions for students, teachers, and administrators.
- **Classroom Management**: Course enrollments, assignments, and resource sharing.
- **Timetable**: Section-specific weekly schedules.
- **Announcements & Messaging**: Real-time communication within schools and courses.
- **Lost & Found Module**: Dedicated gallery and reporting system for lost or found items with automated potential-match notifications.

## Lost & Found Module

The Lost & Found module introduces several new API endpoints, which are protected by `@school_scoped`:
- `GET /lost-found/gallery`: Gallery Dashboard with search and filters (category, location, type).
- `GET /lost-found/my-items`: User Profile View to manage own items.
- `GET/POST /lost-found/report`: Submission Form for new lost/found items.
- `POST /lost-found/resolve/<item_id>`: Endpoint to mark an item as returned/resolved.

**Image Storage Handling:**
Currently, image uploads for Lost & Found items are handled via **local storage**. Files are saved to `static/uploads/lost_found/` with a securely generated filename combining the user ID and a timestamp. In a production environment with heavier traffic, this should be migrated to an external blob storage provider such as AWS S3.

## Folder Structure
```text
.
├── app/                # Core application package
│   ├── routes/         # Flask Blueprints (auth, dashboard, classroom)
│   ├── models.py       # SQLAlchemy database models
│   ├── middleware.py   # Tenant isolation & RBAC logic
│   └── __init__.py     # Application factory
├── static/             # Frontend assets (CSS, JS)
├── templates/          # HTML templates
├── run.py              # Application entry point
├── .env.example        # Environment variable template
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## Installation Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/vaibhav/Code-JAM.git
   cd Code-JAM
   ```
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/scripts/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
5. **Initialize the database**:
   ```bash
   python init_db.py
   ```
6. **Run the application**:
   ```bash
   python run.py
   ```

## Usage Instructions
- Access the application at `http://127.0.0.1:5000`.
- Log in with credentials provided by your institution.

## Contribution Guidelines
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# 🔌 Hive Plugin System Design Document

> **Status**: Proposed  
> **Goal**: Design a highly extensible, secure, and developer-friendly plugin system for Hive that satisfies all PRD requirements without modifying Hive Core.

---

## 1. Requirements Recap

To achieve the "WordPress of campus platforms" vision, plugins must be able to:
1. Register Flask blueprints (for full page UI).
2. Add sidebar items (navigation).
3. Define permissions (for RBAC integration).
4. Create database tables (extend the schema).
5. Add templates (and override existing ones).
6. Expose REST APIs.
7. **Crucially**: Achieve all of this without modifying a single line of Hive Core.

---

## 2. Architectural Comparison

We have three primary ways to implement a plugin system in a Flask/Python ecosystem.

### Architecture A: Python Package Entry Points (The Native Python Way)
Plugins are standard Python packages published to PyPI or installed locally via `pip`. Hive discovers them using `importlib.metadata.entry_points`.

*   **How it works**: A plugin's `pyproject.toml` defines an entry point under a `hive.plugins` group. Hive scans this group on startup and initializes the registered classes.
*   **Pros**: Uses standard Python packaging; native dependency management (pip resolves dependencies); excellent for production environments.
*   **Cons**: High barrier to entry for student developers (must learn Python packaging); requires server restart and command-line access (`pip install`) to add a plugin; hard to "hot-disable" from a web UI without uninstalling the package.

### Architecture B: Pluggy (The Pytest Way)
Uses `pluggy`, the hook-calling mechanism built for `pytest`. Core defines a `Hookspec` (e.g., `hookspec.add_blueprints()`), and plugins implement `hookimpl(add_blueprints)`.

*   **How it works**: Hive declares 50+ hooks. Plugins register hook implementations. When Hive starts, it calls `plugin_manager.hook.add_blueprints()`, aggregating the results.
*   **Pros**: Extremely robust; strict contract enforcement; supports 1-to-N hook relationships cleanly.
*   **Cons**: Can become "spaghetti" if not carefully managed; adding DB models via hooks is clunky in SQLAlchemy; steeper learning curve for beginners compared to object-oriented inheritance.

### Architecture C: Directory-based Manifest + Base Class (The WordPress/Django Way)
Plugins are just folders placed in a `plugins/` directory. Each folder contains a `plugin.json` manifest and a Python file inheriting from a `HivePlugin` base class.

*   **How it works**: Hive scans the `plugins/` folder for `plugin.json`. It dynamically imports the module, instantiates the subclass, and calls standard lifecycle methods (`register_blueprints()`, `get_models()`, etc.).
*   **Pros**: **Lowest barrier to entry** (just drop a folder and edit a JSON file); easy to enable/disable via the database/UI; keeps all plugin assets (templates, CSS) neatly isolated in one folder.
*   **Cons**: Dependency management is harder (if a plugin requires a 3rd-party pip package, Hive must manage installing it); requires dynamic `importlib` manipulation.

---

## 3. Recommendation

**I recommend Architecture C: Directory-based Manifest + Base Class, augmented with `blinker` signals for event hooking.**

**Why?** The primary goal of Hive is rapid community adoption, especially among student developers. Architecture C provides the "WordPress experience." A student can copy a `hello_world` plugin folder, tweak the Python file, and see it appear in their Hive dashboard instantly. 

We mitigate the Python dependency issue by standardizing a `requirements.txt` inside the plugin folder, which the Hive CLI can parse during installation.

---

## 4. Deep Dive into the Recommended Architecture

### 4.1 Folder Structure

A plugin lives in the `/plugins/` directory at the root of the Hive repository (but gitignored).

```text
hive-root/
└── plugins/
    └── library_management/
        ├── plugin.json          # Metadata and basic config
        ├── requirements.txt     # Python dependencies (if any)
        ├── __init__.py          # Contains the HivePlugin subclass
        ├── models.py            # SQLAlchemy models
        ├── routes.py            # UI Blueprints
        ├── api.py               # REST API endpoints
        ├── templates/           # Plugin-specific Jinja templates
        │   └── library/
        └── migrations/          # Alembic revisions for this plugin
```

### 4.2 The Manifest (`plugin.json`)

The manifest allows Hive to display the plugin in the Admin UI *without* executing its Python code (safe discovery).

```json
{
  "name": "Library Management",
  "slug": "library_management",
  "version": "1.0.0",
  "description": "Add book tracking, lending, and fines to Hive.",
  "author": "Luca The Dev",
  "entry_point": "plugin:LibraryPlugin",
  "hive_version": ">=2.0.0",
  "nav_items": [
    {
      "label": "Library",
      "icon": "menu_book",
      "url_endpoint": "library.dashboard",
      "permissions": ["library.view"]
    }
  ],
  "permissions": {
    "library.view": "View the library catalog",
    "library.manage": "Add books and manage fines"
  }
}
```

### 4.3 The Base Class Contract

Hive Core exposes a `HivePlugin` base class. Plugins inherit this to interact with the core.

```python
# hive/core/plugins/base.py
class HivePlugin:
    def __init__(self, app, manifest):
        self.app = app
        self.manifest = manifest

    def register_blueprints(self) -> list:
        """Return a list of Flask Blueprints to be registered."""
        return []

    def register_api_blueprints(self) -> list:
        """Return a list of flask-smorest Blueprints for the /api/v1/ tree."""
        return []

    def get_template_folder(self) -> str:
        """Return the absolute path to the plugin's template folder."""
        return None

    def on_enable(self):
        """Called when the admin enables the plugin in the UI."""
        pass

    def on_disable(self):
        """Called when the admin disables the plugin in the UI."""
        pass
```

### 4.4 Fulfilling the Requirements

#### 1. Registering Flask Blueprints & REST APIs
The plugin creates standard Flask blueprints. The base class returns them. Hive Core's plugin manager registers them during `create_app()`.

```python
# plugins/library_management/plugin.py
from hive.core.plugins.base import HivePlugin
from .routes import library_bp
from .api import library_api_bp

class LibraryPlugin(HivePlugin):
    def register_blueprints(self):
        return [library_bp]  # e.g., url_prefix='/library'
        
    def register_api_blueprints(self):
        return [library_api_bp] # e.g., url_prefix='/api/v1/plugins/library'
```

#### 2. Adding Sidebar Items
This is handled purely through `plugin.json` (see manifest above). Hive's template (`_sidebar.html`) reads the active plugins from the database, parses their manifests, and injects the `nav_items` into the UI if the current user has the required permissions.

#### 3. Defining Permissions
Also handled via `plugin.json`. When a plugin is enabled, Hive's Plugin Manager reads the `"permissions"` block and injects them into the global `PERMISSIONS` registry. Admins can then assign `library.manage` to the "Librarian" role via the standard UI.

#### 4. Creating Database Tables (The tricky part)
We cannot just append to core migrations, nor can we use `db.create_all()` in production. 
**Solution: Multiple Alembic Branches.**
Alembic supports multiple migration branches. 
1. The plugin defines its models in `models.py` importing `db` from `hive.extensions`.
2. The plugin has its own `migrations/` folder.
3. Hive CLI provides a command: `hive plugin makemigrations library_management`. This tells Alembic to generate a migration script *specifically for this plugin's branch*, stored in the plugin's folder.
4. On startup, Hive runs `flask db upgrade` which upgrades the core branch and all active plugin branches.

#### 5. Adding Templates
The Plugin Manager registers the plugin's `templates/` folder with Flask's template loader using `app.jinja_loader`. 
To avoid name collisions, plugins MUST namespace their templates (e.g., `templates/library_management/index.html`).
Because Flask searches loaders in order, a Plugin can even override a Core template by placing a file at `templates/core/dashboard.html` (if we allow this via a strict override priority queue).

#### 6. Not Modifying Core
Everything is dynamically loaded. The database tracks which plugins are active (`PluginState` table: `id, slug, is_active, version`). During Flask's `create_app()`, Hive queries this table, dynamically imports the active plugins, and hooks them into the app *before* the first request is served.

### 4.5 Event Hooks (Blinker)

What if the Library plugin wants to charge a fine when a student pays their tuition? It shouldn't modify the Fees module. Instead, it listens to signals.

Hive Core uses the `blinker` library to broadcast events:

```python
# hive/core/events.py
from blinker import Namespace
hive_signals = Namespace()

fee_paid_event = hive_signals.signal('fee-paid')
```

The plugin subscribes to it in its `__init__`:

```python
# plugins/library_management/plugin.py
from hive.core.events import fee_paid_event

class LibraryPlugin(HivePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Connect to the core signal
        fee_paid_event.connect(self.handle_fee_paid)

    def handle_fee_paid(self, sender, **kwargs):
        student_id = kwargs.get('student_id')
        # Logic to deduct library fines from the fee payment
```

---

## 5. Plugin Lifecycle Management

1.  **Install**: Admin uploads a `.zip` or runs `hive plugin install <github-url>`. Hive extracts it to `/plugins/`, parses `plugin.json`, installs pip requirements, and registers it in the DB as `inactive`.
2.  **Enable**: Admin clicks "Enable". Hive runs the plugin's Alembic migrations, calls `plugin.on_enable()`, and marks it `active`. (Requires server reload/Gunicorn restart to register blueprints).
3.  **Disable**: Admin clicks "Disable". Hive marks it `inactive`. Routes are unregistered on next server reload. Tables remain intact.
4.  **Uninstall**: Admin clicks "Uninstall". Hive runs Alembic downgrade for the plugin's branch (dropping tables safely), then deletes the folder.

## 6. Summary of Execution

This Directory + Base Class + Blinker architecture provides the ultimate balance. It protects Hive Core from modification, respects Flask's application factory pattern, safely manages database schemas via Alembic branching, and provides an exceptionally low barrier to entry for student and open-source contributors.

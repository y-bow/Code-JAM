# Hive Plugin Development Guide

> **Version**: v1.0 — Release Candidate
> **Reference**: [Plugin Design.md](Plugin%20Design.md)

This guide explains how to create, package, and distribute plugins for Hive.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Plugin Structure](#2-plugin-structure)
3. [The `plugin.json` Manifest](#3-the-pluginjson-manifest)
4. [Entry Point](#4-entry-point)
5. [Registering Blueprints](#5-registering-blueprints)
6. [Hooking into Events](#6-hooking-into-events)
7. [Plugin Lifecycle](#7-plugin-lifecycle)
8. [Installing Plugins](#8-installing-plugins)
9. [Example: Hello World Plugin](#9-example-hello-world-plugin)
10. [Best Practices](#10-best-practices)

---

## 1. Overview

Hive's plugin system allows third-party developers to add new functionality without modifying core files. Plugins are discovered via a `plugin.json` manifest in the `plugins/` directory.

**Key principles:**

- Plugins register independently via Python entry points
- Plugins cannot modify Hive Core files
- Plugins are removable without breaking the system
- Plugins support version compatibility declarations

---

## 2. Plugin Structure

Every plugin lives in its own directory under `plugins/`:

```text
plugins/
└── my_plugin/
    ├── plugin.json          # Required: Manifest file
    ├── __init__.py          # Required: Entry point with Plugin class
    ├── templates/           # Optional: Jinja2 templates
    ├── static/              # Optional: Static assets (CSS, JS, images)
    └── requirements.txt     # Optional: Additional Python dependencies
```

---

## 3. The `plugin.json` Manifest

The manifest tells Hive about your plugin:

```json
{
    "name": "My Plugin",
    "slug": "my_plugin",
    "version": "1.0.0",
    "description": "What my plugin does.",
    "author": "Your Name",
    "entry_point": "plugin:MyPlugin",
    "min_hive_version": "0.1.0"
}
```

| Field             | Required | Description                                    |
|-------------------|----------|------------------------------------------------|
| `name`            | Yes      | Human-readable display name                    |
| `slug`            | Yes      | Machine-readable identifier (directory name)   |
| `version`         | Yes      | Semantic version of the plugin                 |
| `description`     | No       | Short description shown in admin panel         |
| `author`          | No       | Author/organization name                       |
| `entry_point`     | Yes      | Python module path and class (`module:Class`)  |
| `min_hive_version`| No       | Minimum Hive version required                  |

> The `slug` must match the directory name. Hive uses the directory name as the plugin identifier.

---

## 4. Entry Point

The entry point is a Python class that inherits from `HivePlugin`:

```python
from app.core.plugins.base import HivePlugin

class MyPlugin(HivePlugin):
    def register_blueprints(self):
        """Return a list of Flask Blueprints to register."""
        return []

    def get_template_folder(self):
        """Return the path to an optional templates folder."""
        return None

    def on_enable(self):
        """Called when the plugin is activated."""
        pass

    def on_disable(self):
        """Called when the plugin is deactivated."""
        pass
```

The entry point path in `plugin.json` uses the format `module_path:ClassName`. For a file at `plugins/my_plugin/__init__.py` with class `MyPlugin`, the entry point is:

```json
"entry_point": "plugin:MyPlugin"
```

---

## 5. Registering Blueprints

To add new routes, create a Flask Blueprint and return it from `register_blueprints()`:

```python
from flask import Blueprint, render_template_string
from app.core.plugins.base import HivePlugin

my_bp = Blueprint('my_plugin', __name__, url_prefix='/my-plugin')

@my_bp.route('/')
def index():
    return render_template_string('<h1>My Plugin</h1>')

class MyPlugin(HivePlugin):
    def register_blueprints(self):
        return [my_bp]
```

Hive automatically registers all returned blueprints when the plugin is activated.

---

## 6. Hooking into Events

Hive emits events via the `blinker` library. Plugins can subscribe to these events to run custom logic:

### Available Signals

All signals are defined in `app/events.py`:

| Signal                 | Description                            |
|------------------------|----------------------------------------|
| `user_logged_in`       | Fired after a user successfully logs in|
| `user_registered`      | Fired after a new user registers       |
| `course_enrolled`      | Fired when a student enrolls in a course|
| `fee_paid`             | Fired when a fee payment is completed  |
| `announcement_posted`  | Fired when an announcement is created  |
| `timetable_updated`    | Fired when a timetable entry changes   |

### Subscribing to Events

```python
from app.events import user_logged_in

def send_welcome_notification(user, **kwargs):
    # user is the User object that logged in
    print(f"Welcome back, {user.name}!")

user_logged_in.connect(send_welcome_notification)
```

### Connecting in `on_enable`

Always connect and disconnect signals in the lifecycle methods:

```python
from app.events import user_logged_in

class MyPlugin(HivePlugin):
    def on_enable(self):
        user_logged_in.connect(self._on_login)

    def on_disable(self):
        user_logged_in.disconnect(self._on_login)

    def _on_login(self, sender, user, **kwargs):
        self.app.logger.info(f"Plugin: {user.name} logged in")
```

---

## 7. Plugin Lifecycle

The lifecycle is managed via the **Plugin Manager** (`app/core/plugins/__init__.py`):

1. **Discovery**: Hive scans `plugins/` for `plugin.json` files on startup
2. **Database Check**: Queries `plugin_states` table for active plugins
3. **Activation**: For each active plugin, imports the entry point, instantiates the class, calls `on_enable()`, and registers blueprints
4. **Runtime**: Plugin handles requests and responds to events
5. **Deactivation**: Admin toggles plugin off via the panel; blueprints are removed
6. **Uninstall**: Plugin record is removed from `plugin_states` table

> Blueprint registration happens at startup. Toggling a plugin requires a server restart to take effect for blueprints. Event handlers can be connected/disconnected at runtime.

---

## 8. Installing Plugins

### Via Admin Panel

1. Place your plugin folder in `plugins/`
2. Go to **Admin > Plugins** (`/admin/plugins`)
3. Click **Install** next to the plugin
4. The plugin appears and is activated

### Via CLI

```bash
# Copy plugin into the plugins/ directory
cp -r my_plugin plugins/

# Create the database record manually (if needed)
flask shell
>>> from app.models import db, PluginState
>>> record = PluginState(slug='my_plugin', is_active=True, version='1.0.0')
>>> db.session.add(record)
>>> db.session.commit()
```

> After installing via CLI, restart the server for blueprints to load.

---

## 9. Example: Hello World Plugin

The Hello World sample plugin is included in the Hive repository at `plugins/hello_world/`.

**`plugins/hello_world/plugin.json`**:
```json
{
    "name": "Hello World",
    "version": "1.0.0",
    "description": "A sample plugin that demonstrates the Hive plugin system.",
    "author": "Hive Team",
    "entry_point": "plugin:HelloWorldPlugin",
    "min_hive_version": "0.1.0"
}
```

**`plugins/hello_world/__init__.py`**:
```python
from flask import Blueprint, render_template_string
from app.core.plugins.base import HivePlugin

hello_bp = Blueprint('hello_world', __name__, url_prefix='/hello')

@hello_bp.route('/')
def index():
    return render_template_string('''
        <h2>Hello from Hello World Plugin!</h2>
        <p>This page is served by a Hive plugin.</p>
    ''')

class HelloWorldPlugin(HivePlugin):
    def register_blueprints(self):
        return [hello_bp]

    def on_enable(self):
        self.app.logger.info('HelloWorld plugin enabled')

    def on_disable(self):
        self.app.logger.info('HelloWorld plugin disabled')
```

---

## 10. Best Practices

- **Keep plugins focused**: Each plugin should do one thing well
- **Use `on_enable`/`on_disable`**: Always clean up event handlers and resources
- **Prefix URLs**: Use a unique URL prefix per plugin to avoid route conflicts
- **Declare dependencies**: Specify `min_hive_version` to prevent compatibility issues
- **No core modifications**: Never modify files outside your plugin directory
- **Log activity**: Use `self.app.logger` for consistent logging
- **Handle errors gracefully**: Catch exceptions to avoid crashing the host application
- **Follow naming conventions**: Use snake_case for slugs, PascalCase for class names

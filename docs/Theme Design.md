# 🎨 Hive Theme Engine Design Document

> **Status**: Proposed  
> **Scope**: Theme Engine Architecture for Hive (v2.0+)  
> **References**: [Architectural Analysis](file:///c:/Users/vaibh/.gemini/antigravity-ide/brain/47b463ba-3a30-43af-81e5-ed62ceca9c3a/hive_architectural_analysis.md), [PRD](file:///c:/Users/vaibh/.gemini/antigravity-ide/brain/47b463ba-3a30-43af-81e5-ed62ceca9c3a/hive_prd.md), [Plugin Architecture](file:///c:/Users/vaibh/.gemini/antigravity-ide/brain/47b463ba-3a30-43af-81e5-ed62ceca9c3a/hive_plugin_design.md)

---

## 1. Design Goals

1. **Separation of Concerns**: Themes dictate presentation, never business logic.
2. **Cascading Overrides**: Institutions can override a single CSS variable, a specific template, or the entire application layout.
3. **Upgrade Resilience**: Core updates to modules should not break custom themes unless fundamental structural changes occur.
4. **Zero-Touch Branding**: Admins can brand the platform (logos, colors) via the settings UI without writing code or creating a theme.
5. **No Build Step Required**: Themes use native CSS variables and vanilla JS. No Webpack or SCSS required for end-users, lowering the barrier to entry.

## 2. Theme Directory Structure

Themes reside in the `/themes/` directory at the project root.

```text
themes/
├── default/                      # The core, fallback theme
│   ├── theme.json
│   ├── templates/
│   │   ├── base.html             # Master layout
│   │   ├── auth/
│   │   │   └── login.html        # Login page override
│   │   ├── dashboard/
│   │   │   └── index.html        # Dashboard customization
│   │   └── frontend/
│   │       └── landing.html      # Landing page customization
│   └── static/
│       ├── css/
│       │   ├── variables.css     # CSS custom properties contract
│       │   └── theme.css         # Structural styling
│       ├── js/
│       ├── fonts/                # Custom fonts
│       └── images/               # Theme-specific images
│
└── campus_modern/                # A custom, third-party theme
    ├── theme.json
    ├── templates/
    │   └── auth/
    │       └── login.html        # Only overrides login, inherits rest
    └── static/
        └── css/
            └── variables.css     # Overrides colors and fonts
```

## 3. Theme Loading Lifecycle

1. **Initialization**: During Flask `create_app()`, Hive reads the `active_theme` from `SiteSetting`.
2. **Manifest Parsing**: The engine parses `/themes/<active_theme>/theme.json`.
3. **Template Loader Injection**: Hive configures a `jinja2.ChoiceLoader`.
4. **Static Blueprint Registration**: Hive registers a dynamic blueprint to serve `/theme/static/<path>` pointing to the active theme's static folder.
5. **Request Phase**: When a view calls `render_template('auth/login.html')`, Jinja searches the loader chain.
6. **Branding Injection**: The `base.html` template fetches branding settings from the DB and injects them as inline CSS variables to override the theme's default variables.

## 4. Template Inheritance Strategy

Hive uses a **Cascading Choice Loader**. Jinja2 will look for templates in the following order:

1. `themes/<active_theme>/templates/` (Active Theme)
2. `themes/<parent_theme>/templates/` (Parent Theme, if defined in `theme.json`)
3. `modules/<module_name>/templates/` (Module Defaults)
4. `themes/default/templates/` (Core Fallback)

**Override Strategy**: 
If an institution wants a custom login page, they create `themes/my_theme/templates/auth/login.html`. Hive uses this instead of the core auth module's template. Because they did not create `dashboard/index.html`, Hive falls back to the core module's dashboard template.

**Macro Usage**: 
To ensure update compatibility, core UI components (buttons, cards, inputs) are abstracted into Jinja macros (`ui.html`). Themes can override the macro file to instantly restyle all components system-wide.

## 5. CSS Variable System

The contract between Hive Core and any Theme is a set of CSS Custom Properties prefixed with `--hive-`.

**The Contract (`variables.css`)**:
```css
:root {
  /* Colors */
  --hive-primary: #2563eb;
  --hive-bg-main: #ffffff;
  --hive-text-main: #0f172a;
  
  /* Typography */
  --hive-font-sans: 'Inter', system-ui, sans-serif;
  
  /* Layout */
  --hive-sidebar-width: 260px;
  --hive-radius-md: 8px;
}
```

**Light/Dark Mode**:
Themes implement dark mode using a data attribute on the `<html>` tag, toggled via vanilla JS stored in localStorage.

```css
html[data-theme="dark"] {
  --hive-bg-main: #000000;
  --hive-text-main: #f8fafc;
}
```

## 6. Branding System

The Branding System operates independently of themes. It allows UI-based customization stored in the `SiteSetting` database table.

**Settings**:
- `branding.logo_url`
- `branding.favicon_url`
- `branding.primary_color`
- `branding.institution_name`

**Injection Mechanism**:
In `themes/default/templates/base.html`, these settings are injected as a `<style>` block *after* the theme's CSS is loaded, forcing a CSS variable override.

```html
<style>
  :root {
    {% if get_setting('branding.primary_color') %}
    --hive-primary: {{ get_setting('branding.primary_color') }};
    {% endif %}
  }
</style>
```

## 7. Asset Management

- **Theme Assets**: Served via `/theme/static/`. This route dynamically maps to `themes/<active_theme>/static/`. This allows templates to safely reference `<link href="{{ url_for('theme_static', filename='css/variables.css') }}">` without hardcoding the theme name.
- **Custom Logos**: Uploaded via the Settings UI, stored in `instance/uploads/branding/`, and served via a dedicated media route.
- **Custom Fonts**: Themes can include `.woff2` files in their `static/fonts/` directory and define `@font-face` rules in `variables.css`.

## 8. Configuration Format

**`theme.json`**:
```json
{
  "name": "Campus Modern",
  "slug": "campus_modern",
  "version": "1.0.0",
  "author": "Hive Community",
  "hive_version": ">=2.0.0",
  "parent": "default",
  "features": {
    "dark_mode": true,
    "custom_colors": true
  }
}
```

## 9. Theme Compatibility Strategy

To prevent a theme from breaking when Hive updates:
1. **Semantic Versioning Limit**: `theme.json` declares `"hive_version": ">=2.0.0, <3.0.0"`. If an admin upgrades Hive to v3.0 (a major UI rewrite), incompatible themes are automatically disabled, falling back to `default`.
2. **Stable CSS Classes**: Core templates use utility classes sparingly. Structural classes (e.g., `.hive-sidebar`, `.hive-card`, `.hive-table`) are guaranteed stable across minor versions.
3. **Data Attributes over Classes for JS**: Core JavaScript relies on `data-action="..."` rather than CSS classes for event listeners, ensuring themes can rename classes without breaking interactivity.

## 10. Upgrade Strategy

When Hive Core is updated (e.g., v2.1 to v2.2):
1. **Fallback Protection**: If a theme overrides `login.html` and v2.2 introduces a new required field (e.g., MFA token), the old theme template will crash.
2. **Detection**: Hive's template renderer catches `TemplateRuntimeError`.
3. **Failsafe**: If a custom theme throws an error rendering a core view, Hive logs the error and gracefully re-renders using the `default` theme template as a failsafe, preventing a hard outage.

## 11. Security Considerations

1. **Path Traversal Protection**: The `/theme/static/<path>` route must sanitize the path using `werkzeug.security.safe_join` to prevent escaping the theme's static folder.
2. **XSS Prevention in Branding**: Any user-provided CSS (like primary color) must be validated via regex (e.g., `^#[0-9A-Fa-f]{6}$`) before injection into the inline `<style>` block to prevent CSS injection attacks.
3. **No Executable Code**: Themes cannot contain Python code. `theme.json` is purely declarative.

## 12. Example Theme Structure (Child Theme)

An institution that only wants to change the login page layout and the font:

```text
themes/
└── my_college/
    ├── theme.json               # Sets "parent": "default"
    ├── templates/
    │   └── auth/
    │       └── login.html       # Total redesign of the login screen
    └── static/
        └── css/
            └── variables.css    # Overrides --hive-font-sans
```

## 13. Future Improvements

- **Theme Customizer UI**: A live-preview interface in the admin panel to adjust CSS variables visually.
- **Marketplace Integration**: One-click installation of community themes directly from the admin dashboard.
- **Dynamic Asset Compilation**: Server-side SCSS compilation for advanced themes that require math/color-mixing beyond native CSS `color-mix()` capabilities.

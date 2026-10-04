# Hive Theme Development Guide

> **Version**: v1.0 — Release Candidate
> **Reference**: [Theme Design.md](Theme%20Design.md)

This guide explains how to create, customize, and distribute themes for Hive.

---

## Table of Contents

1. [Overview](#1-overview)
2. [How Theming Works](#2-how-theming-works)
3. [CSS Variable System](#3-css-variable-system)
4. [Configuration via Admin Panel](#4-configuration-via-admin-panel)
5. [Toggling Light/Dark Mode](#5-toggling-lightdark-mode)
6. [Theme Defaults and Overrides](#6-theme-defaults-and-overrides)
7. [CSS Customization](#7-css-customization)
8. [Branding Settings](#8-branding-settings)
9. [Future: Directory-based Themes](#9-future-directory-based-themes)
10. [Best Practices](#10-best-practices)

---

## 1. Overview

Hive's theme system uses **CSS Custom Properties** (CSS variables) to control the appearance of the entire application. Institutions can customize colors and light/dark mode defaults without writing code, simply by updating settings in the admin panel.

---

## 2. How Theming Works

The current theme engine operates through two mechanisms:

### 2.1 Server-side Default

Hive stores two theme-related settings in its `SiteSetting` key-value store:

| Setting Key             | Purpose                       | Default  |
|-------------------------|-------------------------------|----------|
| `theme.active`          | Default theme mode            | `light`  |
| `theme.primary_color`   | Primary brand color (hex)     | `#2563eb`|

These settings are read on every page load and injected into `base.html` as inline CSS variables and the body class.

### 2.2 Client-side Toggle

Users can toggle between light and dark mode using the theme toggle button in the top bar. The preference is stored in `localStorage` as `hive-theme`. The initial value defaults to the server-side `theme.active` setting if no local preference exists.

---

## 3. CSS Variable System

The core visual contract is defined by CSS custom properties in the `:root` block of `styles.css`:

```css
:root {
    --primary-color: #2563eb;
    --primary-rgb: 37, 99, 235;
    --primary-light: #60a5fa;
    --primary-dark: #1d4ed8;
    --secondary-color: #3b82f6;
    --accent-color: #0ea5e9;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
    --bg-main: #ffffff;
    --bg-glass: rgba(255, 255, 255, 0.7);
    --text-main: #0f172a;
    --text-muted: #64748b;
    --border-color: rgba(226, 232, 240, 0.8);
    --font-heading: 'Outfit', sans-serif;
    --font-body: 'Inter', sans-serif;
    --sidebar-width: 260px;
    --radius-sm: 8px;
    --radius-md: 16px;
    --radius-lg: 24px;
}
```

### Dark Mode Overrides

Dark mode variables are applied via the `body.dark-theme` class:

```css
body.dark-theme {
    --primary-color: #dc2626;
    --primary-rgb: 220, 38, 38;
    --bg-main: #000000;
    --bg-glass: rgba(20, 20, 20, 0.8);
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --border-color: rgba(50, 50, 50, 0.8);
}
```

### Server-side Variable Injection

In `base.html`, the primary color setting is injected after the main CSS:

```html
<style>
    :root {
        --primary-color: {{ get_setting('theme.primary_color', '#2563eb') }};
        --primary-rgb: {{ get_setting('theme.primary_color', '#2563eb') | hex_to_rgb }};
        --primary-light: color-mix(in srgb, {{ pc }}, white 30%);
        --primary-dark: color-mix(in srgb, {{ pc }}, black 20%);
    }
</style>
```

This overrides the defaults in `styles.css`, allowing admins to change colors dynamically.

---

## 4. Configuration via Admin Panel

The settings page at `/admin/settings` provides:

### Theme Mode Selector

Choose the default theme mode for all users:

- **Light** — Light background, dark text
- **Dark** — Dark background, light text

Users can still toggle individually; this sets the default for first-time visitors.

### Primary Color Picker

Enter a hex color code (e.g., `#2563eb` for blue) to set the institution's brand color. This value is used for:

- Navigation link highlights
- Button backgrounds
- Avatar gradients
- Focus ring outlines
- Active element indicators

---

## 5. Toggling Light/Dark Mode

### End Users

Click the theme toggle button (sun/moon icon) in the top bar. The preference is saved to `localStorage` and persists across sessions.

### Implementation Details

The toggle is handled in `static/js/app.js`:

```javascript
const savedTheme = localStorage.getItem('hive-theme');
if (savedTheme) {
    body.className = savedTheme;
}
updateThemeIcon(body.className);

themeToggleBtn.addEventListener('click', () => {
    if (body.classList.contains('light-theme')) {
        body.classList.replace('light-theme', 'dark-theme');
        localStorage.setItem('hive-theme', 'dark-theme');
    } else {
        body.classList.replace('dark-theme', 'light-theme');
        localStorage.setItem('hive-theme', 'light-theme');
    }
    updateThemeIcon(body.className);
});
```

---

## 6. Theme Defaults and Overrides

The precedence for theme values is:

1. **Admin Settings** (`theme.active`, `theme.primary_color`) — stored in DB
2. **Inline CSS** in `base.html` — injected from settings
3. **`styles.css`** `:root` block — fallback defaults
4. **`body.dark-theme`** block — dark mode overrides
5. **User `localStorage`** — client-side toggle preference

This means the admin can set a default, the user can override it locally, and the CSS always has sensible fallbacks.

---

## 7. CSS Customization

### Overriding Variables in Custom CSS

To further customize Hive's appearance, add CSS overrides to `static/css/styles.css` or inject a custom stylesheet:

```css
/* Example: Custom brand colors */
:root {
    --primary-color: #7c3aed;
    --primary-rgb: 124, 58, 237;
    --font-heading: 'Poppins', sans-serif;
}

body.dark-theme {
    --bg-main: #0f0f23;
    --text-main: #e0e0ff;
}
```

### Important Notes

- Use `var(--primary-color)` etc. instead of hardcoded colors for future-proofing
- The `--primary-rgb` variable must be maintained alongside `--primary-color` for `rgba()` usage
- The `color-mix()` function is used for `--primary-light` and `--primary-dark` and is supported in all modern browsers

---

## 8. Branding Settings

Branding is handled independently from theming:

| Setting                     | Purpose                    | Access                    |
|-----------------------------|----------------------------|---------------------------|
| `theme.primary_color`       | Brand color (hex)          | Admin Settings            |
| `theme.active`              | Default light/dark mode    | Admin Settings            |
| Logo (light/dark)           | Institution logos          | File: `static/images/`    |
| Favicon                     | Browser tab icon           | File: `static/favicon.png`|

> Logo images are stored at `static/images/light_theme.png` and `static/images/dark_theme.png`. Replace these files to customize branding.

---

## 9. Future: Directory-based Themes

The current theme engine injects CSS variables server-side and supports light/dark mode toggling. Future versions will introduce full **directory-based themes** where a complete theme package lives under `themes/`:

```text
themes/
├── default/                  # Core fallback theme
│   ├── theme.json
│   ├── templates/
│   │   └── base.html
│   └── static/
│       └── css/
│           └── variables.css
└── my_college/              # Custom theme
    ├── theme.json
    ├── templates/
    │   └── auth/
    │       └── login.html
    └── static/
        └── css/
            └── variables.css
```

This will allow:

- Complete template overrides
- Custom fonts and icon sets
- Theme inheritance and parent themes
- One-click installation from a marketplace

See [Theme Design.md](Theme%20Design.md) for the full architecture.

---

## 10. Best Practices

- **Use CSS variables**: Reference `var(--primary-color)` instead of hardcoding colors
- **Support both modes**: Always define both `:root` (light) and `body.dark-theme` overrides
- **Respect the system**: Don't override structural classes (`.hive-sidebar`, `.hive-card`)
- **Test accessibility**: Ensure color contrast ratios meet WCAG 2.1 AA standards
- **Keep branding separate**: Institution logos and names should use the settings system, not hardcoded HTML
- **Avoid inline styles**: Use CSS classes and variables for maintainability

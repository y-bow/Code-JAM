# Agents

This file contains information and instructions for the opencode agents working on this project.

## Common Commands

| Command | Description |
|---------|-------------|
| `python run.py` | Start the development server |
| `python init_db.py` | Initialize the database with seed data |
| `pip install -r requirements.txt` | Install project dependencies |

## Agent Instructions

- Follow the project's code conventions.
- Use the existing testing patterns.
- Always run relevant tests after making changes.
- If you find a useful command, add it to the "Common Commands" section above.
- **Context Management**: If your context usage reaches approximately 70%, read this file to identify files that should be ignored to optimize context usage.

## Unnecessary or Temporary Files

Ignore the following files/directories to save context:

- `__pycache__/`
- `tmp/`
- `section*.json`
- `instance/app.db`
- `.venv/`
- `venv/`

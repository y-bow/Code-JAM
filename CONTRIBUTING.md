# Contributing to Code-JAM

First off, thank you for considering contributing to Code-JAM! It's people like you that make the open-source community such an amazing place to learn, inspire, and create.

## First Time Setup

After cloning, run this once to clean your local git cache:

    git rm --cached -r --ignore-unmatch __pycache__/
    find . -name "*.pyc" -exec git rm --cached --ignore-unmatch {} \;
    git pull origin main

## Local Database

Never commit instance/app.db — it is gitignored.
After pulling, if models.py or init_db.py changed,
rebuild your local database:

    python init_db.py

This wipes local data and reseeds fresh.
You will never see pycache or app.db in git status,
git diff, or PRs ever again after this fix.

## How Can I Contribute?

### Reporting Bugs
* Check the existing issues to see if the bug has already been reported.
* If not, open a new issue with a clear title and description, including steps to reproduce the bug.

### Suggesting Enhancements
* Open a new issue and describe the enhancement you'd like to see and why it would be useful.

### Pull Requests
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Make your changes and commit them: `git commit -m 'Add some feature'`.
4. Push to the branch: `git push origin feature-name`.
5. Open a pull request.

## Code of Conduct
Please be respectful and professional in your interactions with other contributors.

## Project Structure
* `app/`: Core application logic, models, and routes.
* `static/`: Frontend assets (CSS, JS, images).
* `templates/`: HTML templates.

## Rules
* Follow the project's coding style and folder structure.
* Ensure all dependencies are open-source.
* Do not commit sensitive information (passwords, API keys).

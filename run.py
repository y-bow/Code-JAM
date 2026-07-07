import os
import sys
from flask_migrate import upgrade
from app import create_app, db
from app.models import User

app = create_app()

def database_needs_seeding():
    try:
        user_count = User.query.count()
        return user_count == 0
    except Exception:
        return True

def auto_seed():
    print("Database is empty or reseed requested. Preparing to seed...")
    from init_db import seed_all
    seed_all()
    print("Auto-seed complete.")

with app.app_context():
    upgrade()

    force_reseed = '--reseed' in sys.argv
    if database_needs_seeding() or force_reseed:
        if force_reseed:
            print("Force reseed requested via --reseed flag...")
        auto_seed()
    else:
        print("Database already seeded. Skipping auto-seed.")
        print("Run 'python run.py --reseed' to force a fresh seed.")

if __name__ == '__main__':
    if '--reseed' in sys.argv:
        sys.argv.remove('--reseed')
    app.run(host='0.0.0.0', port=5000, debug=True)
import os
import sys
from flask_migrate import upgrade
from app import create_app, db
from app.models import User

app = create_app()
print(f"[run.py] SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')}")
print(f"[run.py] Instance path = {app.instance_path}")

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

def is_development():
    return os.environ.get('FLASK_ENV', 'development') == 'development'

with app.app_context():
    from app import db
    for bind_key, engine in db.engines.items():
        print(f"[run.py] Engine bind={bind_key!r} url={engine.url}")
    if not db.engines:
        print(f"[run.py] No engines registered yet. db.engine = {db.engine.url}")
    upgrade()

    force_reseed = '--reseed' in sys.argv
    if force_reseed:
        if is_development():
            print("Force reseed requested via --reseed flag...")
            auto_seed()
        else:
            print("--reseed is only allowed in development mode. Set FLASK_ENV=development.")
            sys.exit(1)
    elif is_development() and database_needs_seeding():
        auto_seed()
    else:
        print("Skipping auto-seed. Use the setup wizard at /setup/ to configure your institution.")
        print("Run with --reseed (development only) for demo data.")

if __name__ == '__main__':
    if '--reseed' in sys.argv:
        sys.argv.remove('--reseed')
    app.run(host='0.0.0.0', port=5000, debug=is_development())

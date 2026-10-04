import os
import sys
from flask_migrate import upgrade
from app import create_app, db

app = create_app()
print(f"[run.py] SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')}")
print(f"[run.py] Instance path = {app.instance_path}")

def is_development():
    return os.environ.get('FLASK_ENV', 'development') == 'development'

with app.app_context():
    from app import db
    for bind_key, engine in db.engines.items():
        print(f"[run.py] Engine bind={bind_key!r} url={engine.url}")
    if not db.engines:
        print(f"[run.py] No engines registered yet. db.engine = {db.engine.url}")
    upgrade()

    if '--reseed' in sys.argv:
        if is_development():
            print("Force reseed requested via --reseed flag...")
            from init_db import seed_all
            seed_all()
            from app.services.setup_service import mark_setup_complete
            mark_setup_complete()
            print("Reseed complete. Setup marked as complete for demo data.")
        else:
            print("--reseed is only allowed in development mode. Set FLASK_ENV=development.")
            sys.exit(1)
    else:
        print("Database is empty. The setup wizard will guide you through initial configuration.")
        print("Run with --reseed (development only) for demo data.")

if __name__ == '__main__':
    if '--reseed' in sys.argv:
        sys.argv.remove('--reseed')
    app.run(host='0.0.0.0', port=5000, debug=is_development())

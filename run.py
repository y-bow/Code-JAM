import os
import sys
from app import create_app, db
from app.models import User

app = create_app()

def database_needs_seeding():
    try:
        # Check if users table has any data
        user_count = User.query.count()
        return user_count == 0
    except Exception:
        # Table doesn't exist yet
        return True

def auto_seed():
    print("Database is empty or reseed requested. Preparing to seed...")
    # Import and run seed function from init_db
    from init_db import seed_all
    
    # Ensure tables exist
    db.metadata.drop_all(bind=db.engine)
    db.create_all()
    
    seed_all()
    print("Auto-seed complete.")

# Initialize database logic before running the app
with app.app_context():
    # Always ensure tables are created (creates if missing)
    db.create_all()
    
    force_reseed = '--reseed' in sys.argv
    if database_needs_seeding() or force_reseed:
        if force_reseed:
            print("Force reseed requested via --reseed flag...")
        auto_seed()
    else:
        print("Database already seeded. Skipping auto-seed.")
        print("Run 'python run.py --reseed' to force a fresh seed.")

if __name__ == '__main__':
    # Remove --reseed from sys.argv before passing to Flask/Click
    if '--reseed' in sys.argv:
        sys.argv.remove('--reseed')
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    if not users:
        print("No users found in the database.")
    else:
        for user in users:
            print(f"Email: {user.email}, Role: {user.role}, Active: {user.is_active}")

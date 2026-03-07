from app import create_app
from app.models import User
app = create_app()
with app.app_context():
    users = User.query.all()
    print("\n--- Users in Database ---")
    for u in users:
        print(f"Email: {u.email}, Role: {u.role}")
    print("------------------------\n")

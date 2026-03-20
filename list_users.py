from app import create_app
from app.models import db, User

app = create_app()
with app.app_context():
    users = User.query.all()
    print("Name | Email | Role")
    print("-" * 50)
    for user in users:
        print(f"{user.name} | {user.email} | {user.role}")

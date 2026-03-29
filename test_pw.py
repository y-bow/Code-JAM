from app import create_app
from app.models import User, bcrypt

app = create_app()
with app.app_context():
    # Test vaibhav login
    email = 'vaibhav.b-29@scds.saiuniversity.edu.in'
    password = 'hive@1234'
    user = User.query.filter_by(email=email).first()
    if user:
        is_correct = bcrypt.check_password_hash(user.password_hash, password)
        print(f"User: {email}")
        print(f"Password 'hive@1234' check: {is_correct}")
    else:
        print(f"User {email} not found.")

    # Test admin login
    email = 'admin@hive.lms'
    user = User.query.filter_by(email=email).first()
    if user:
        is_correct = bcrypt.check_password_hash(user.password_hash, password)
        print(f"User: {email}")
        print(f"Password 'hive@1234' check: {is_correct}")
    else:
        print(f"User {email} not found.")


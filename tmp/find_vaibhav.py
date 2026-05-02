import os
import sys
# Set PYTHONPATH to the current directory
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User, Student

app = create_app()
with app.app_context():
    email = 'vaibhav.b-29@scds.saiuniversity.edu.in'.lower()
    user = User.query.filter(User.email.ilike(email)).first()
    if user:
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            print(f"User ID: {user.id}")
            print(f"Name: {user.name}")
            print(f"Role: {user.role}")
            print(f"Section ID: {student.section_id}")
            print(f"School ID: {user.school_id}")
            print(f"Current CGPA: {student.cgpa}")
        else:
            print(f"User found, but no Student profile: {user.id} ({user.role})")
    else:
        print("User not found")

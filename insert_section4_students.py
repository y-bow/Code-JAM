import os
import json
from app import create_app
from app.models import db, School, Section, User, Student, bcrypt

def insert_section4_students():
    app = create_app()
    with app.app_context():
        # Find School and Section
        scds_school = School.query.filter_by(code='SCDS').first()
        if not scds_school:
            print("Error: SCDS school not found.")
            return
        
        section4 = Section.query.filter_by(code='SCDS-CS-S4', school_id=scds_school.id).first()
        if not section4:
            print("Error: Section 4 (SCDS-CS-S4) not found.")
            # Let's try to find by name if code fails
            section4 = Section.query.filter_by(name='Section 4', school_id=scds_school.id).first()
            if not section4:
                print("Error: Section 4 not found by name either.")
                return

        print(f"Adding students to {scds_school.name}, {section4.name} (ID: {section4.id})")

        # Load students from JSON
        with open('section4_students.json', 'r') as f:
            students_data = json.load(f)

        pw_hash = bcrypt.generate_password_hash("hive@1234").decode('utf-8')
        
        added_count = 0
        skipped_count = 0

        for s_data in students_data:
            email = s_data['email']
            name = s_data['name']
            
            existing = User.query.filter_by(email=email).first()
            if existing:
                print(f"Skipping: User {email} already exists.")
                skipped_count += 1
                continue
            
            user = User(
                school_id=scds_school.id,
                email=email,
                password_hash=pw_hash,
                role='student',
                name=name
            )
            db.session.add(user)
            db.session.flush() # Get user.id
            
            student_profile = Student(
                user_id=user.id,
                section_id=section4.id,
                enrollment_year=2025,
                major="Computer Science"
            )
            db.session.add(student_profile)
            added_count += 1
            print(f"Added student: {name} ({email})")

        db.session.commit()
        print(f"\nFinished! Added {added_count} students to Section 4, skipped {skipped_count}.")

if __name__ == "__main__":
    insert_section4_students()

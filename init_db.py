import json
import random
import os
from app import create_app
from app.models import (
    db, User, Student, Teacher, School, Section,
    Course, Enrollment, TimetableEntry, bcrypt,
    ProfessorAssistant
)
from datetime import datetime

app = create_app()

def load_demo_data():
    demo_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'demo.json')
    with open(demo_path, 'r') as f:
        return json.load(f)

def generate_student(school_id, section_id, enrollment_year, demo_data, email_counter):
    first_name = random.choice(demo_data['first_names'])
    last_name = random.choice(demo_data['last_names'])
    name = f"{first_name} {last_name}"
    email = f"student{email_counter}@demo.edu"
    pw = bcrypt.generate_password_hash('hive@1234').decode('utf-8')
    
    user = User(school_id=school_id, email=email,
                password_hash=pw, role='student', name=name, must_change_password=True)
    db.session.add(user)
    db.session.flush()
    
    lab_sec = random.randint(1, 5)
    student = Student(user_id=user.id, section_id=section_id, enrollment_year=enrollment_year, major='Computer Science', lab_section=lab_sec)
    db.session.add(student)
    return user

def seed_school():
    print("Seeding schools...")
    soe = School(name='School of Engineering', code='SOE', domain='soe.demo.edu')
    soa = School(name='School of Arts', code='SOA', domain='soa.demo.edu')
    sob = School(name='School of Business', code='SOB', domain='sob.demo.edu')
    
    db.session.add_all([soe, soa, sob])
    db.session.commit()
    return soe, soa

def seed_staff(school):
    print("Seeding staff...")
    pw = bcrypt.generate_password_hash('hive@1234').decode('utf-8')
    
    admin = User(school_id=None, email='admin@demo.edu',
                 password_hash=pw, role='admin', name='System Admin')
    superadmin = User(school_id=None, email='superadmin@demo.edu',
                      password_hash=pw, role='superadmin', name='Super Admin')
    
    dean = User(school_id=school.id, email='dean@soe.demo.edu',
                password_hash=pw, role='dean', name='Dr. Jane Dean')
    prof = User(school_id=school.id, email='professor@soe.demo.edu',
                password_hash=pw, role='professor', name='Prof. John Doe')
    assistant = User(school_id=school.id, email='assistant@soe.demo.edu',
                     password_hash=pw, role='assistant_professor', name='Asst. Prof. Alex')
    
    db.session.add_all([admin, superadmin, dean, prof, assistant])
    db.session.commit()
    
    db.session.add_all([
        Teacher(user_id=prof.id, department='Computer Science'),
        Teacher(user_id=assistant.id, department='Computer Science')
    ])
    db.session.commit()
    return prof

def seed_sections_and_students(school, demo_data):
    print("Seeding sections and students...")
    sections = []
    student_counter = 1
    for i in range(1, 8):
        sec = Section(school_id=school.id, name=f'Section {i}', code=f'SOE-CS-S{i}', batch_year=2025)
        db.session.add(sec)
        db.session.commit()
        sections.append(sec)
        
        for _ in range(demo_data['students_per_section']):
            generate_student(school.id, sec.id, 2025, demo_data, student_counter)
            student_counter += 1
        db.session.commit()
    return sections

def seed_timetable_for_section(section, teacher_user):
    courses_to_create = [
        ("Discrete Mathematics", "CS-301", 4),
        ("Introduction to Programming", "CS-101", 4),
        ("Data Structures", "CS-201", 4),
        ("Algorithms", "CS-302", 4),
    ]
    
    section_courses = {}
    for name, code, credits in courses_to_create:
        course = Course(
            section_id=section.id,
            name=name,
            code=code,
            teacher_id=teacher_user.id,
            credits=credits
        )
        db.session.add(course)
        db.session.flush()
        section_courses[name] = course

    entries_data = [
        (0, "09:00 AM", "10:30 AM", "Discrete Mathematics", "Room 101", "#cfe2f3"),
        (0, "10:40 AM", "12:10 PM", "Introduction to Programming", "Room 102", "#ead1dc"),
        (1, "09:00 AM", "10:30 AM", "Data Structures", "Room 103", "#f9cb9c"),
        (2, "10:40 AM", "12:10 PM", "Algorithms", "Room 104", "#d9ead3"),
        (3, "02:15 PM", "03:40 PM", "Discrete Mathematics", "Room 101", "#cfe2f3"),
        (4, "09:00 AM", "10:30 AM", "Introduction to Programming", "Room 102", "#ead1dc"),
    ]

    for day, start, end, title, room, color in entries_data:
        course = section_courses.get(title)
        entry = TimetableEntry(
            section_id=section.id,
            course_id=course.id if course else None,
            day=day,
            start_time=start,
            end_time=end,
            title=title,
            teacher=teacher_user.name,
            room=room,
            color=color,
            status='active'
        )
        db.session.add(entry)
    db.session.commit()

def seed_all():
    demo_data = load_demo_data()
    soe_school, soa_school = seed_school()
    prof = seed_staff(soe_school)
    
    sections = seed_sections_and_students(soe_school, demo_data)
    
    print("Seeding timetables...")
    for sec in sections:
        seed_timetable_for_section(sec, prof)
        
    print("All data seeded successfully.")

if __name__ == "__main__":
    with app.app_context():
        print("Dropping and recreating all tables for a fresh seed...")
        db.metadata.drop_all(bind=db.engine)
        db.create_all()
        seed_all()
        print("Database initialized successfully.")

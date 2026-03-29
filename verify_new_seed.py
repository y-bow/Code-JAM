from app import create_app
from app.models import User, Student, Section, Course, TimetableEntry

app = create_app()
with app.app_context():
    total_users = User.query.count()
    s1 = Section.query.filter_by(code='SCDS-CS-S1').first()
    s2 = Section.query.filter_by(code='SCDS-CS-S2').first()
    s3 = Section.query.filter_by(code='SCDS-CS-S3').first()
    
    s1_count = Student.query.filter_by(section_id=s1.id).count() if s1 else 0
    s2_count = Student.query.filter_by(section_id=s2.id).count() if s2 else 0
    s3_count = Student.query.filter_by(section_id=s3.id).count() if s3 else 0
    
    timetable_count = TimetableEntry.query.count()
    course_count = Course.query.count()
    
    print(f"Total Users: {total_users}")
    print(f"Section 1 Students: {s1_count}")
    print(f"Section 2 Students: {s2_count}")
    print(f"Section 3 Students: {s3_count}")
    print(f"Total Courses: {course_count}")
    print(f"Timetable Entries: {timetable_count}")
    
    # Check a few specific students
    v_s3 = User.query.filter_by(email='vaibhav.b-29@scds.saiuniversity.edu.in').first()
    if v_s3 and v_s3.student_profile:
        print(f"Vaibhav (S3) Lab Section: {v_s3.student_profile.lab_section}")
    else:
        print("Error: Vaibhav (S3) could not be found.")

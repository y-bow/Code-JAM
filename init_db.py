from app import create_app
from app.models import (
    db, User, Student, Teacher, School, Section,
    Course, Enrollment, Announcement, TimetableEntry,
    TeacherTodo, TeacherRating, FriendRequest, Friendship,
    ClassRep, bcrypt
)
from datetime import datetime, timedelta

app = create_app()


def seed_db():
    with app.app_context():
        # Drop and recreate all tables
        db.metadata.drop_all(bind=db.engine)
        db.create_all()
        print("Tables created.")

        # =====================================================================
        # 1. SCHOOL
        # =====================================================================
        school = School(
            name='Sai University - School of Computing and Data Science',
            code='SCDS',
            domain='scds.saiuniversity.edu.in'
        )
        school_soai = School(
            name='Sai University - School of Artificial Intelligence',
            code='SOAI',
            domain='soai.saiuniversity.edu.in'
        )
        db.session.add_all([school, school_soai])
        db.session.commit()
        print(f"Schools created: {school.name}, {school_soai.name}")

        # =====================================================================
        # 2. SECTIONS
        # =====================================================================
        sec2 = Section(school_id=school.id, name='Section 2', code='SEC-2', batch_year=2025)
        sec3 = Section(school_id=school.id, name='Section 3', code='SEC-3', batch_year=2025)
        sec4 = Section(school_id=school.id, name='Section 4', code='SEC-4', batch_year=2025)
        sec_soai_1 = Section(school_id=school_soai.id, name='SOAI Section 1', code='SOAI-SEC1', batch_year=2025)
        db.session.add_all([sec2, sec3, sec4, sec_soai_1])
        db.session.commit()
        print(f"Sections created: SEC-2, SEC-3, SEC-4, SOAI-SEC1")

        # =====================================================================
        # 3. USERS
        # =====================================================================
        pw = bcrypt.generate_password_hash('password123').decode('utf-8')

        admin = User(school_id=school.id, email='admin@scds.saiuniversity.edu.in',
                     password_hash=pw, role='superadmin', name='Super Admin')
        dean = User(school_id=school.id, email='dean@scds.saiuniversity.edu.in',
                    password_hash=pw, role='dean', name='Dr. Dean Kumar')
        teacher1 = User(school_id=school.id, email='prof.smith@scds.saiuniversity.edu.in',
                        password_hash=pw, role='teacher', name='Prof. John Smith')
        teacher2 = User(school_id=school.id, email='prof.davis@scds.saiuniversity.edu.in',
                        password_hash=pw, role='teacher', name='Prof. Sarah Davis')

        # Students SCDS
        vaibhav = User(school_id=school.id, email='vaibhav.b-29@scds.saiuniversity.edu.in',
                       password_hash=pw, role='student', name='Vaibhav B')
        sharan = User(school_id=school.id, email='sharanpranav.a-29@scds.saiuniversity.edu.in',
                      password_hash=pw, role='student', name='Sharanpranav A')
        harshitha = User(school_id=school.id, email='harshitha.b-29@scds.saiuniversity.edu.in',
                         password_hash=pw, role='student', name='Harshitha B')
        riddhima = User(school_id=school.id, email='ruddhima.p-29@scds.saiuniversity.edu.in',
                        password_hash=pw, role='student', name='Riddhima P')

        # SOAI Users
        greeta = User(school_id=school_soai.id, email='greeta@soai.saiuniversity.edu.in',
                      password_hash=pw, role='teacher', name='Greeta')
        siddharth = User(school_id=school_soai.id, email='siddharth@soai.saiuniversity.edu.in',
                         password_hash=pw, role='teacher', name='Siddharth')
        siddanth = User(school_id=school_soai.id, email='siddanth@soai.saiuniversity.edu.in',
                        password_hash=pw, role='teacher', name='Siddanth')
        pankaj = User(school_id=school_soai.id, email='pankaj@soai.saiuniversity.edu.in',
                      password_hash=pw, role='teacher', name='Pankaj')
        arun_kumar = User(school_id=school_soai.id, email='arun.kumar@soai.saiuniversity.edu.in',
                          password_hash=pw, role='teacher', name='Arun Kumar')
        sadhana = User(school_id=school_soai.id, email='sadhana.s-29@soai.saiuniversity.edu.in',
                       password_hash=pw, role='student', name='Sadhana Srinivasan')

        all_users = [admin, dean, teacher1, teacher2, vaibhav, sharan, harshitha, riddhima,
                     greeta, siddharth, siddanth, pankaj, arun_kumar, sadhana]
        db.session.add_all(all_users)
        db.session.commit()
        print(f"Users created: {len(all_users)}")

        # =====================================================================
        # 4. PROFILES
        # =====================================================================
        t1 = Teacher(user_id=teacher1.id, department='Computer Science', office_hours='Mon/Wed 10am-12pm')
        t2 = Teacher(user_id=teacher2.id, department='Mathematics', office_hours='Tue/Thu 2pm-4pm')
        db.session.add_all([t1, t2])

        # SOAI Teachers
        soai_teachers = [
            Teacher(user_id=greeta.id, department='Artificial Intelligence'),
            Teacher(user_id=siddharth.id, department='Humanities'),
            Teacher(user_id=siddanth.id, department='Social Sciences'),
            Teacher(user_id=pankaj.id, department='Computer Science'),
            Teacher(user_id=arun_kumar.id, department='Mathematics'),
        ]
        db.session.add_all(soai_teachers)

        # Student profiles — assigned to correct sections
        student_sections = [
            (vaibhav, sec3),      # Vaibhav B → Section 3
            (sharan, sec4),       # Sharanpranav A → Section 4
            (harshitha, sec2),    # Harshitha B → Section 2
            (riddhima, sec2),     # Riddhima P → Section 2
            (sadhana, sec_soai_1), # Sadhana Srinivasan → SOAI Section 1
        ]
        for user, section in student_sections:
            cgpa = 8.8 if user == vaibhav else 0.0
            sgpa = 8.8 if user == vaibhav else 0.0
            db.session.add(Student(user_id=user.id, section_id=section.id,
                                   enrollment_year=2025, major='Computer Science',
                                   cgpa=cgpa, sgpa=sgpa))

        db.session.commit()
        print("Profiles and Class Reps created.")

        # =====================================================================
        # 5. COURSES (under sections)
        # =====================================================================
        # Section 3 courses
        s3_courses = [
            Course(section_id=sec3.id, name='Discrete Mathematics', code='MATH201', teacher_id=teacher2.id, credits=4, meet_link='https://meet.google.com/abc-defg-hij'),
            Course(section_id=sec3.id, name='Indian Constitution and Democracy', code='POL101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec3.id, name='Python and Data Structure', code='CS102', teacher_id=teacher1.id, credits=4, meet_link='https://meet.google.com/xyz-pdqr-mno'),
            Course(section_id=sec3.id, name='Introduction to Data Structures', code='CS201', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec3.id, name='Programming in Python', code='CS101', teacher_id=teacher1.id, credits=3),
            Course(section_id=sec3.id, name='Environment and Sustainability', code='ENV101', teacher_id=teacher2.id, credits=3),
        ]
        db.session.add_all(s3_courses)

        # Section 4 courses
        s4_courses = [
            Course(section_id=sec4.id, name='Indian Constitution and Democracy', code='POL101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec4.id, name='Discrete Mathematics', code='MATH201', teacher_id=teacher2.id, credits=4),
            Course(section_id=sec4.id, name='PDS Lab Sec4', code='CS102L', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec4.id, name='Introduction to Data Structures', code='CS201', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec4.id, name='Programming in Python', code='CS101', teacher_id=teacher1.id, credits=3),
            Course(section_id=sec4.id, name='Environment and Sustainability', code='ENV101', teacher_id=teacher2.id, credits=3),
        ]
        db.session.add_all(s4_courses)

        # Section 2 courses
        s2_courses = [
            Course(section_id=sec2.id, name='Discrete Mathematics', code='MATH201', teacher_id=teacher2.id, credits=4),
            Course(section_id=sec2.id, name='Programming in Python', code='CS101', teacher_id=teacher1.id, credits=3),
            Course(section_id=sec2.id, name='Introduction to Data Structures', code='CS201', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec2.id, name='Environment and Sustainability', code='ENV101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec2.id, name='Indian Constitution and Democracy', code='POL101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec2.id, name='Python and Data Structure', code='CS102', teacher_id=teacher1.id, credits=4),
        ]
        db.session.add_all(s2_courses)

        # SOAI Courses
        soai_courses = [
            Course(section_id=sec_soai_1.id, name='DS in C Lab', code='AI101L', teacher_id=greeta.id, credits=2),
            Course(section_id=sec_soai_1.id, name='AI in Programming', code='AI101', teacher_id=greeta.id, credits=4),
            Course(section_id=sec_soai_1.id, name='Critical Thinking', code='HUM101', teacher_id=siddharth.id, credits=3),
            Course(section_id=sec_soai_1.id, name='AI Programming Lab', code='AI102L', teacher_id=greeta.id, credits=2),
            Course(section_id=sec_soai_1.id, name='Intro to Embedded Systems and Robotics', code='AI201', teacher_id=greeta.id, credits=4),
            Course(section_id=sec_soai_1.id, name='Data Structures', code='AI202', teacher_id=greeta.id, credits=4),
            Course(section_id=sec_soai_1.id, name='Indian Constitution', code='POL102', teacher_id=siddanth.id, credits=3),
            Course(section_id=sec_soai_1.id, name='OOP\'s', code='AI203', teacher_id=pankaj.id, credits=4),
            Course(section_id=sec_soai_1.id, name='P&S', code='MATH102', teacher_id=arun_kumar.id, credits=4),
        ]
        db.session.add_all(soai_courses)
        db.session.commit()
        print("Courses created with meet links.")

        # =====================================================================
        # 6. ENROLLMENTS
        # =====================================================================
        # Enroll Vaibhav in all Sec3 courses
        for c in s3_courses:
            db.session.add(Enrollment(student_id=vaibhav.id, course_id=c.id))
        # Enroll Sharan in all Sec4 courses
        for c in s4_courses:
            db.session.add(Enrollment(student_id=sharan.id, course_id=c.id))
        # Enroll Harshitha and Riddhima in all Sec2 courses
        for c in s2_courses:
            db.session.add(Enrollment(student_id=harshitha.id, course_id=c.id))
            db.session.add(Enrollment(student_id=riddhima.id, course_id=c.id))
        # Enroll Sadhana in all SOAI courses
        for c in soai_courses:
            db.session.add(Enrollment(student_id=sadhana.id, course_id=c.id))
        db.session.commit()
        print("Enrollments created.")

        # =====================================================================
        # 7. TIMETABLE ENTRIES
        # =====================================================================
        # --- Section 3 timetable ---
        sec3_timetable = [
            (0, '10:40 AM', '12:10 PM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (0, '02:15 PM', '03:40 PM', 'Indian Constitution and Democracy', 'AB2 - 202', '#a78bfa'),
            (0, '03:50 PM', '05:15 PM', 'Python and Data Structure (LAB)', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (1, '09:00 AM', '10:30 AM', 'Introduction to Data Structures', 'AB1 - 101', 'var(--success-color)'),
            (1, '12:15 PM', '01:45 PM', 'Environment and Sustainability', 'AB1 - Moot Court Hall', 'var(--warning-color)'),
            (2, '09:00 AM', '10:30 AM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (2, '02:15 PM', '03:40 PM', 'Indian Constitution and Democracy', 'AB2 - 207', '#a78bfa'),
            (3, '09:00 AM', '10:30 AM', 'Programming in Python', 'AB2 - 207', '#f472b6'),
            (3, '12:20 PM', '01:40 PM', 'Python and Data Structure (LAB)', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (4, '10:40 AM', '12:10 PM', 'Programming in Python', 'AB2 - 202', '#f472b6'),
            (4, '02:15 PM', '03:40 PM', 'Introduction to Data Structures', 'AB2 - 202', 'var(--success-color)'),
            (4, '03:50 PM', '05:15 PM', 'Environment and Sustainability', 'AB2 - 202', 'var(--warning-color)'),
        ]
        for day, st, et, title, room, color in sec3_timetable:
            db.session.add(TimetableEntry(section_id=sec3.id, day=day,
                           start_time=st, end_time=et, title=title, room=room, color=color))

        # --- Section 2 timetable ---
        sec2_timetable = [
            (0, '09:00 AM', '10:40 AM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (0, '10:40 AM', '12:10 PM', 'Indian Constitution and Democracy', 'AB2 - 202', '#a78bfa'),
            (0, '02:15 PM', '03:40 PM', 'Environment and Sustainability', 'AB2 - Mini Auditorium', 'var(--success-color)'),
            (1, '09:00 AM', '10:30 AM', 'Programming in Python', 'AB2 - 202', 'var(--warning-color)'),
            (1, '12:20 PM', '01:40 PM', 'Python and Data Structure (LAB)', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (2, '10:00 AM', '11:30 AM', 'Indian Constitution and Democracy', 'AB2 - 101', '#a78bfa'),
            (2, '12:40 PM', '02:05 PM', 'Introduction to Data Structures', 'AB1 - Moot Court Hall', 'var(--warning-color)'),
            (2, '02:15 PM', '03:40 PM', 'Environment and Sustainability', 'AB2 - Mini Auditorium', 'var(--success-color)'),
            (3, '10:00 AM', '11:30 AM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (3, '01:40 PM', '03:05 PM', 'Programming in Python', 'AB2 - 101', 'var(--warning-color)'),
            (4, '10:40 AM', '12:10 PM', 'Python and Data Structure (LAB)', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (4, '12:40 PM', '02:05 PM', 'Introduction to Data Structures', 'AB2 - 202', 'var(--warning-color)'),
        ]
        for day, st, et, title, room, color in sec2_timetable:
            db.session.add(TimetableEntry(section_id=sec2.id, day=day,
                           start_time=st, end_time=et, title=title, room=room, color=color))

        # --- Section 4 timetable ---
        sec4_timetable = [
            (0, '09:00 AM', '10:30 AM', 'Indian Constitution and Democracy', 'AB2-202', '#a78bfa'),
            (0, '01:40 PM', '03:05 PM', 'Programming in Python', 'AB2-101', '#f472b6'),
            (1, '09:00 AM', '10:30 AM', 'Discrete Mathematics', 'AB1-104', 'var(--primary-color)'),
            (1, '03:50 PM', '05:15 PM', 'Environment and Sustainability', 'AB2 - 207', 'var(--warning-color)'),
            (2, '09:00 AM', '10:30 AM', 'PDS Lab', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (2, '10:40 AM', '12:10 PM', 'Introduction to Data Structures', 'AB2 - 202', 'var(--success-color)'),
            (2, '01:40 PM', '03:05 PM', 'Programming in Python', 'AB2 - 203', '#f472b6'),
            (3, '09:00 AM', '10:30 AM', 'Introduction to Data Structures', 'AB2-101', 'var(--success-color)'),
            (3, '10:40 AM', '12:10 PM', 'PDS Lab', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (3, '12:40 PM', '02:05 PM', 'Indian Constitution and Democracy', 'AB1 - 104', '#a78bfa'),
            (4, '10:35 AM', '12:05 PM', 'Environment and Sustainability', 'AB2 - 101', 'var(--warning-color)'),
            (4, '02:15 PM', '03:40 PM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
        ]
        for day, st, et, title, room, color in sec4_timetable:
            db.session.add(TimetableEntry(section_id=sec4.id, day=day,
                           start_time=st, end_time=et, title=title, room=room, color=color))

        # --- SOAI Section 1 timetable ---
        soai_timetable = [
            # Monday
            (0, '09:00 AM', '10:30 AM', 'DS in C Lab', 'AB1 LAB', 'var(--accent-color)'),
            (0, '12:40 PM', '02:05 PM', 'AI in Programming', 'AB1 101', '#f472b6'),
            (0, '03:50 PM', '05:15 PM', 'Critical Thinking', 'AB2 101', '#a78bfa'),
            # Tuesday
            (1, '09:00 AM', '10:30 AM', 'AI Programming Lab', 'AB1 LAB', 'var(--accent-color)'),
            (1, '10:40 AM', '12:10 PM', 'Introduction to Embedded Systems and Robotics', 'AB2 203', 'var(--warning-color)'),
            (1, '12:40 PM', '02:05 PM', 'Data Structures', 'AB1 101', 'var(--success-color)'),
            (1, '02:15 PM', '03:40 PM', 'Introduction to Embedded Systems and Robotics', 'AB2 207', 'var(--warning-color)'),
            # Wednesday
            (2, '09:00 AM', '10:30 AM', 'Indian Constitution and Democracy', 'AB2 - 202', '#a78bfa'),
            (2, '10:40 AM', '12:10 PM', 'Object Oriented Programming\'s', 'Moot court', 'var(--primary-color)'),
            (2, '12:40 PM', '02:05 PM', 'AI in Programming', 'AB1 101', '#f472b6'),
            # Thursday
            (3, '09:00 AM', '10:30 AM', 'Critical Thinking', 'AB2 - 202', '#a78bfa'),
            (3, '10:40 AM', '12:10 PM', 'Data Structures', 'AB1 - 101', 'var(--success-color)'),
            (3, '02:15 PM', '03:40 PM', 'Indian Constitution and Democracy', 'Mini Auditorium', '#a78bfa'),
            (3, '03:50 PM', '05:15 PM', 'P&S', 'AB2 - 203', 'var(--danger-color)'),
            # Friday
            (4, '09:00 AM', '10:30 AM', 'P&S', 'AB2 - 203', 'var(--danger-color)'),
            (4, '10:40 AM', '12:10 PM', 'Object Oriented Programming\'s', 'AB1 - 101', 'var(--primary-color)'),
        ]
        for day, st, et, title, room, color in soai_timetable:
            db.session.add(TimetableEntry(section_id=sec_soai_1.id, day=day,
                           start_time=st, end_time=et, title=title, room=room, color=color))

        db.session.commit()
        print("Timetable entries seeded.")

        # =====================================================================
        # 8. TEACHER TASKS & RATINGS
        # =====================================================================
        db.session.add_all([
            TeacherTodo(teacher_id=teacher1.id, title='Grade Python Assignment 1'),
            TeacherTodo(teacher_id=teacher1.id, title='Prepare Data Structures Slides', is_completed=True),
            TeacherRating(student_id=vaibhav.id, teacher_id=teacher1.id, course_id=s3_courses[2].id, rating=5, review='Excellent professor! Extremely clear explanations.'),
            TeacherRating(student_id=sharan.id, teacher_id=teacher1.id, course_id=s4_courses[2].id, rating=4, review='Great lab sessions.')
        ])

        # =====================================================================
        # 9. SOCIAL (Friends)
        # =====================================================================
        db.session.add_all([
            FriendRequest(sender_id=sharan.id, recipient_id=vaibhav.id, status='accepted'),
            Friendship(user1_id=sharan.id, user2_id=vaibhav.id),
            FriendRequest(sender_id=harshitha.id, recipient_id=vaibhav.id, status='pending')
        ])

        # =====================================================================
        # 10. SAMPLE ANNOUNCEMENTS
        # =====================================================================
        a1 = Announcement(school_id=school.id, course_id=None, teacher_id=dean.id,
                          title='Welcome to the new semester!',
                          body='Classes begin on March 10. Check your timetable for details.')
        a2 = Announcement(school_id=school.id, course_id=s3_courses[0].id, teacher_id=teacher2.id,
                          title='Discrete Math Quiz on Friday',
                          body='Chapter 1-3 covered. Bring calculators.', urgent=True)
        db.session.add_all([a1, a2])
        db.session.commit()

        print("\nDatabase seeded successfully!")
        print("\n=== Login Credentials (password: password123) ===")
        print(f"  Admin:      admin@scds.saiuniversity.edu.in")
        print(f"  Dean:       dean@scds.saiuniversity.edu.in")
        print(f"  Teacher1:   prof.smith@scds.saiuniversity.edu.in")
        print(f"  Teacher2:   prof.davis@scds.saiuniversity.edu.in")
        print(f"  Vaibhav B   (SEC-3): vaibhav.b-29@scds.saiuniversity.edu.in")
        print(f"  Sharanpranav A (SEC-4): sharanpranav.a-29@scds.saiuniversity.edu.in")
        print(f"  Harshitha B (SEC-2): harshitha.b-29@scds.saiuniversity.edu.in")
        print(f"  Riddhima P  (SEC-2): ruddhima.p-29@scds.saiuniversity.edu.in")
        print(f"  Sadhana S   (SOAI-SEC1): sadhana.s-29@soai.saiuniversity.edu.in")


if __name__ == '__main__':
    seed_db()

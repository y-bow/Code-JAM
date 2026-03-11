from app import create_app
from app.models import (
    db, User, Student, Teacher, School, Section,
    Course, Enrollment, Announcement, TimetableEntry, bcrypt,
    TeacherTodo, TeacherRating, FriendRequest, Friendship
)
from datetime import datetime

app = create_app()

def seed_db():
    with app.app_context():
        # Drop and recreate all tables
        db.metadata.drop_all(bind=db.engine)
        db.create_all()
        print("Tables created.")

        # =====================================================================
        # 1. SCHOOLS
        # =====================================================================
        school = School(
            name='Sai University - School of Computing and Data Science',
            code='SCDS',
            domain='scds.saiuniversity.edu.in'
        )
        school_soai = School(
            name='Sai University - School of Arts and Sciences',
            code='SOAS',
            domain='soas.saiuniversity.edu.in'
        )
        db.session.add_all([school, school_soai])
        db.session.commit()
        print(f"Schools created: {school.name}, {school_soai.name}")

        # =====================================================================
        # 2. SECTIONS
        # =====================================================================
        sec1 = Section(school_id=school.id, name='Section 1', code='SEC-1', batch_year=2025)
        sec2 = Section(school_id=school.id, name='Section 2', code='SEC-2', batch_year=2025)
        sec3 = Section(school_id=school.id, name='Section 3', code='SEC-3', batch_year=2025)
        sec4 = Section(school_id=school.id, name='Section 4', code='SEC-4', batch_year=2025)
        sec5 = Section(school_id=school.id, name='Section 5', code='SEC-5', batch_year=2025)
        sec_soai_1 = Section(school_id=school_soai.id, name='SOAI Section 1', code='SOAI-SEC1', batch_year=2025)
        
        db.session.add_all([sec1, sec2, sec3, sec4, sec5, sec_soai_1])
        db.session.commit()
        print(f"Sections created: SEC-1 to SEC-5, SOAI-SEC1")

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
        teacher_nitish = User(school_id=school.id, email='nitish@scds.saiuniversity.edu.in',
                              password_hash=pw, role='teacher', name='Nitish')
        teacher_megha = User(school_id=school.id, email='megha.k@scds.saiuniversity.edu.in',
                             password_hash=pw, role='teacher', name='Megha Kapoor')
        teacher_gopi = User(school_id=school.id, email='gopi@scds.saiuniversity.edu.in',
                            password_hash=pw, role='teacher', name='Gopi')
        teacher_beaula = User(school_id=school.id, email='beaula@scds.saiuniversity.edu.in',
                              password_hash=pw, role='teacher', name='Beaula')
        teacher_arjun = User(school_id=school.id, email='arjun@scds.saiuniversity.edu.in',
                             password_hash=pw, role='teacher', name='Arjun')

        # Students
        vaibhav = User(school_id=school.id, email='vaibhav.b-29@scds.saiuniversity.edu.in',
                       password_hash=pw, role='student', name='Vaibhav B')
        sharan = User(school_id=school.id, email='sharanpranav.a-29@scds.saiuniversity.edu.in',
                      password_hash=pw, role='student', name='Sharanpranav A')
        harshitha = User(school_id=school.id, email='harshitha.b-29@scds.saiuniversity.edu.in',
                         password_hash=pw, role='student', name='Harshitha B')
        riddhima = User(school_id=school.id, email='ruddhima.p-29@scds.saiuniversity.edu.in',
                        password_hash=pw, role='student', name='Riddhima P')
        saiteja = User(school_id=school.id, email='saiteja.m-29@scds.saiuniversity.edu.in',
                       password_hash=pw, role='student', name='Mannemala Charan Sai Teja')
        balaaditya = User(school_id=school.id, email='balaaditya.t-29@scds.saiuniversity.edu.in',
                         password_hash=pw, role='student', name='Balaaditya T')

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
        sadhana = User(school_id=school_soai.id, email='sadhana.s@soai.saiuniversity.edu.in',
                       password_hash=pw, role='student', name='Sadhana Srinivasan')

        all_users = [admin, dean, teacher1, teacher2, teacher_nitish, teacher_megha, teacher_gopi, 
                     teacher_beaula, teacher_arjun, vaibhav, sharan, harshitha, riddhima, saiteja, 
                     balaaditya, greeta, siddharth, siddanth, pankaj, arun_kumar, sadhana]
        
        db.session.add_all(all_users)
        db.session.commit()
        print(f"Users created: {len(all_users)}")

        # =====================================================================
        # 4. PROFILES
        # =====================================================================
        t1 = Teacher(user_id=teacher1.id, department='Computer Science', office_hours='Mon/Wed 10am-12pm')
        t2 = Teacher(user_id=teacher2.id, department='Mathematics', office_hours='Tue/Thu 2pm-4pm')
        
        # SOAI Teachers
        soai_teachers = [
            Teacher(user_id=greeta.id, department='Artificial Intelligence'),
            Teacher(user_id=siddharth.id, department='Humanities'),
            Teacher(user_id=siddanth.id, department='Social Sciences'),
            Teacher(user_id=pankaj.id, department='Computer Science'),
            Teacher(user_id=arun_kumar.id, department='Mathematics'),
        ]
        
        # Section 1 Teachers
        sec1_teachers = [
            Teacher(user_id=teacher_nitish.id, department='Computer Science'),
            Teacher(user_id=teacher_megha.id, department='Humanities'),
            Teacher(user_id=teacher_gopi.id, department='Environmental Science'),
            Teacher(user_id=teacher_beaula.id, department='Mathematics'),
            Teacher(user_id=teacher_arjun.id, department='Computer Science'),
        ]
        
        db.session.add_all([t1, t2] + soai_teachers + sec1_teachers)

        # Student profiles
        student_sections = [
            (vaibhav, sec3),      # Vaibhav B → Section 3
            (sharan, sec4),       # Sharanpranav A → Section 4
            (harshitha, sec2),    # Harshitha B → Section 2
            (riddhima, sec2),     # Riddhima P → Section 2
            (saiteja, sec5),      # Sai Teja → Section 5
            (balaaditya, sec1),   # Balaaditya T → Section 1
            (sadhana, sec_soai_1), # Sadhana Srinivasan → SOAI Section 1
        ]
        for user, section in student_sections:
            db.session.add(Student(user_id=user.id, section_id=section.id,
                                   enrollment_year=2025, major='Computer Science'))
        db.session.commit()
        print("Profiles created.")

        # =====================================================================
        # 5. COURSES
        # =====================================================================
        # Section 1 courses
        s1_courses = [
            Course(section_id=sec1.id, name='Introduction to Data Structures', code='CS201', teacher_id=teacher_nitish.id, credits=4),
            Course(section_id=sec1.id, name='Indian Constitution and Democracy', code='POL101', teacher_id=teacher_megha.id, credits=3),
            Course(section_id=sec1.id, name='Environment and Sustainability', code='ENV101', teacher_id=teacher_gopi.id, credits=3),
            Course(section_id=sec1.id, name='Discrete Mathematics', code='MATH201', teacher_id=teacher_beaula.id, credits=4),
            Course(section_id=sec1.id, name='Programming in Python', code='CS101', teacher_id=teacher_arjun.id, credits=3),
            Course(section_id=sec1.id, name='PDS Lab', code='CS101L', teacher_id=teacher_arjun.id, credits=2),
        ]
        
        # Section 2 courses
        s2_courses = [
            Course(section_id=sec2.id, name='Introduction to Data Structures', code='CS201', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec2.id, name='Discrete Mathematics', code='MATH201', teacher_id=teacher2.id, credits=4),
            Course(section_id=sec2.id, name='Programming in Python', code='CS101', teacher_id=teacher1.id, credits=3),
            Course(section_id=sec2.id, name='Environment and Sustainability', code='ENV101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec2.id, name='Indian Constitution and Democracy', code='POL101', teacher_id=teacher2.id, credits=3),
        ]

        # Section 3 courses
        s3_courses = [
            Course(section_id=sec3.id, name='Discrete Mathematics', code='MATH201', teacher_id=teacher2.id, credits=4),
            Course(section_id=sec3.id, name='Indian Constitution and Democracy', code='POL101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec3.id, name='Python and Data Structure', code='CS102', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec3.id, name='Introduction to Data Structures', code='CS201', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec3.id, name='Programming in Python', code='CS101', teacher_id=teacher1.id, credits=3),
            Course(section_id=sec3.id, name='Environment and Sustainability', code='ENV101', teacher_id=teacher2.id, credits=3),
        ]
        
        # Section 4 courses
        s4_courses = [
            Course(section_id=sec4.id, name='Indian Constitution and Democracy', code='POL101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec4.id, name='Discrete Mathematics', code='MATH201', teacher_id=teacher2.id, credits=4),
            Course(section_id=sec4.id, name='PDS Lab Sec4', code='CS102L', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec4.id, name='Introduction to Data Structures', code='CS201', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec4.id, name='Principles of Economics (SAS)', code='ECO101', teacher_id=teacher2.id, credits=3),
        ]
        
        # Section 5 courses
        s5_courses = [
            Course(section_id=sec5.id, name='Introduction to Data Structures', code='CS201', teacher_id=teacher1.id, credits=4),
            Course(section_id=sec5.id, name='Discrete Mathematics', code='MATH201', teacher_id=teacher2.id, credits=4),
            Course(section_id=sec5.id, name='Programming in Python', code='CS101', teacher_id=teacher1.id, credits=3),
            Course(section_id=sec5.id, name='Environment and Sustainability', code='ENV101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec5.id, name='Indian Constitution and Democracy', code='POL101', teacher_id=teacher2.id, credits=3),
            Course(section_id=sec5.id, name='Python and Data Structure (LAB)', code='CS102', teacher_id=teacher1.id, credits=4),
        ]
        
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
        
        db.session.add_all(s1_courses + s2_courses + s3_courses + s4_courses + s5_courses + soai_courses)
        db.session.commit()
        print("Courses created.")

        # =====================================================================
        # 6. ENROLLMENTS
        # =====================================================================
        # Enroll students in their section's courses
        for student, courses in [
            (harshitha, s2_courses), (riddhima, s2_courses),
            (vaibhav, s3_courses), (sharan, s4_courses),
            (saiteja, s5_courses), (balaaditya, s1_courses),
            (sadhana, soai_courses)
        ]:
            for c in courses:
                db.session.add(Enrollment(student_id=student.id, course_id=c.id))
        
        db.session.commit()
        print("Enrollments created.")

        # =====================================================================
        # 7. TIMETABLE ENTRIES
        # =====================================================================
        # Section 1
        sec1_tt = [
            (0, '09:00 AM', '10:30 AM', 'Introduction to Data Structures', 'AB1 - 101', 'var(--success-color)'),
            (0, '12:40 PM', '02:05 PM', 'Indian Constitution and Democracy', 'AB2 - 203', '#a78bfa'),
            (0, '02:15 PM', '03:40 PM', 'Environment and Sustainability', 'AB2 - Mini Auditorium', 'var(--warning-color)'),
            (1, '09:00 AM', '10:30 AM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (1, '03:50 PM', '05:15 PM', 'PDS Lab', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (2, '10:40 AM', '12:10 PM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (2, '12:40 PM', '02:05 PM', 'Programming in Python', 'AB2 - 207', '#f472b6'),
            (2, '02:15 PM', '03:40 PM', 'Environment and Sustainability', 'AB2 - Mini Auditorium', 'var(--warning-color)'),
            (3, '10:40 AM', '12:10 PM', 'Introduction to Data Structures', 'AB1 - Moot Court Hall', 'var(--success-color)'),
            (3, '12:40 PM', '02:05 PM', 'Indian Constitution and Democracy', 'AB2 - 202', '#a78bfa'),
            (4, '10:40 AM', '12:10 PM', 'Programming in Python', 'AB2 - 203', '#f472b6'),
            (4, '02:10 PM', '03:55 PM', 'PDS Lab', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
        ]
        for day, st, et, title, room, color in sec1_tt:
            db.session.add(TimetableEntry(section_id=sec1.id, day=day, start_time=st, end_time=et, title=title, room=room, color=color))

        # Section 2
        sec2_tt = [
            (0, '09:30 AM', '10:40 AM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (0, '10:40 AM', '12:10 PM', 'Indian Constitution and Democracy', 'AB2 - 202', '#a78bfa'),
            (0, '12:15 PM', '01:45 PM', 'Environment and Sustainability', 'AB2 - Mini Auditorium', 'var(--success-color)'),
            (1, '09:00 AM', '10:30 AM', 'Programming in Python', 'AB2 - 202', '#f472b6'),
            (1, '12:20 PM', '01:40 PM', 'Python and Data Structure (LAB)', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (2, '10:00 AM', '11:30 AM', 'Indian Constitution and Democracy', 'AB2 - 101', '#a78bfa'),
            (2, '12:40 PM', '02:05 PM', 'Introduction to Data Structures', 'AB1 - Moot Court Hall', '#ea580c'),
            (2, '02:15 PM', '03:40 PM', 'Environment and Sustainability', 'AB2 - Mini Auditorium', 'var(--success-color)'),
            (3, '10:00 AM', '11:30 AM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (3, '01:40 PM', '03:05 PM', 'Programming in Python', 'AB2 - 101', '#f472b6'),
            (4, '10:40 AM', '12:10 PM', 'Python and Data Structure (LAB)', 'Computer Lab - AB1 - First Floor', 'var(--accent-color)'),
            (4, '12:40 PM', '02:05 PM', 'Introduction to Data Structures', 'AB2 - 202', 'var(--warning-color)'),
        ]
        for day, st, et, title, room, color in sec2_tt:
            db.session.add(TimetableEntry(section_id=sec2.id, day=day, start_time=st, end_time=et, title=title, room=room, color=color))

        # Section 3
        sec3_tt = [
            (0, '10:40 AM', '12:10 PM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (0, '02:15 PM', '03:40 PM', 'Indian Constitution and Democracy', 'AB2 - 202', '#a78bfa'),
            (0, '03:50 PM', '05:15 PM', 'Python and Data Structure (LAB)', 'Computer Lab - AB1 - First Floor', '#d97706'),
            (1, '09:00 AM', '10:30 AM', 'Introduction to Data Structures', 'AB1 - 101', '#ea580c'),
            (1, '12:15 PM', '01:45 PM', 'Environment and Sustainability', 'AB1 - Moot Court Hall', 'var(--success-color)'),
            (2, '09:00 AM', '10:30 AM', 'Discrete Mathematics', 'AB2 - 203', 'var(--primary-color)'),
            (2, '02:15 PM', '03:40 PM', 'Indian Constitution and Democracy', 'AB2 - 207', '#a78bfa'),
            (3, '09:00 AM', '10:30 AM', 'Programming in Python', 'AB2 - 207', '#f97316'),
            (3, '12:20 PM', '01:40 PM', 'Python and Data Structure (LAB)', 'Computer Lab - AB1 - First Floor', '#d97706'),
            (4, '10:40 AM', '12:10 PM', 'Programming in Python', 'AB2 - 202', '#f97316'),
            (4, '02:15 PM', '03:40 PM', 'Introduction to Data Structures', 'AB2 - 202', '#ea580c'),
            (4, '03:50 PM', '05:15 PM', 'Environment and Sustainability', 'AB2 - 202', 'var(--success-color)'),
        ]
        for day, st, et, title, room, color in sec3_tt:
            db.session.add(TimetableEntry(section_id=sec3.id, day=day, start_time=st, end_time=et, title=title, room=room, color=color))

        # Section 5
        sec5_tt = [
            (0, '10:35 AM', '12:05 PM', 'Environment and Sustainability', 'AB1 - 101', 'var(--success-color)'),
            (0, '12:15 PM', '01:45 PM', 'Discrete Mathematics', 'AB1 - 104', 'var(--primary-color)'),
            (0, '02:10 PM', '03:35 PM', 'Python and Data Structure (LAB)', 'Comp Lab', '#ea580c'),
        ]
        for day, st, et, title, room, color in sec5_tt:
            db.session.add(TimetableEntry(section_id=sec5.id, day=day, start_time=st, end_time=et, title=title, room=room, color=color))
        
        db.session.commit()
        print("Timetable entries seeded.")

        # =====================================================================
        # 8. ANNOUNCEMENTS & SOCIAL
        # =====================================================================
        db.session.add_all([
            Announcement(school_id=school.id, teacher_id=dean.id, title='Welcome!', body='Classes start March 10.'),
            Announcement(school_id=school.id, course_id=s3_courses[0].id, teacher_id=teacher2.id, title='Quiz', body='Chapter 1-3 Friday.', urgent=True),
            TeacherTodo(teacher_id=teacher1.id, title='Grade Assignment 1'),
            TeacherRating(student_id=vaibhav.id, teacher_id=teacher1.id, course_id=s3_courses[3].id, rating=5, review='Excellent!'),
            FriendRequest(sender_id=sharan.id, recipient_id=vaibhav.id, status='accepted'),
            Friendship(user1_id=sharan.id, user2_id=vaibhav.id)
        ])
        db.session.commit()

        print("\nDatabase seeded successfully!")
        print("\n=== Login Credentials (password: password123) ===")
        print(f"  Balaaditya T(SEC-1): balaaditya.t-29@scds.saiuniversity.edu.in")
        print(f"  Harshitha B (SEC-2): harshitha.b-29@scds.saiuniversity.edu.in")
        print(f"  Riddhima P  (SEC-2): ruddhima.p-29@scds.saiuniversity.edu.in")
        print(f"  Vaibhav B   (SEC-3): vaibhav.b-29@scds.saiuniversity.edu.in")
        print(f"  Sharan A    (SEC-4): sharanpranav.a-29@scds.saiuniversity.edu.in")
        print(f"  Sai Teja    (SEC-5): saiteja.m-29@scds.saiuniversity.edu.in")
        print(f"  Sadhana S   (SOAI):  sadhana.s@soai.saiuniversity.edu.in")

if __name__ == '__main__':
    seed_db()

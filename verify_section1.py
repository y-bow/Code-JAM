from app import create_app
from app.models import db, School, Section, Student, User

def verify():
    app = create_app()
    with app.app_context():
        scds = School.query.filter_by(code='SCDS').first()
        section1 = Section.query.filter_by(name='Section 1', school_id=scds.id).first()
        
        student_count = Student.query.filter_by(section_id=section1.id).count()
        print(f"Total students in {scds.name}, {section1.name}: {student_count}")
        
        # List first 5 students
        students = Student.query.filter_by(section_id=section1.id).limit(5).all()
        for s in students:
            print(f"- {s.user.name} ({s.user.email})")

if __name__ == "__main__":
    verify()

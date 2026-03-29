from app import create_app
from app.models import db, Section, Student, TimetableEntry

def audit_database():
    app = create_app()
    with app.app_context():
        sections = Section.query.all()
        print(f"{'Section':<15} | {'Students':<10} | {'Timetable':<10}")
        print("-" * 40)
        for s in sections:
            s_count = Student.query.filter_by(section_id=s.id).count()
            t_count = TimetableEntry.query.filter_by(section_id=s.id).count()
            print(f"{s.name:<15} | {s_count:<10} | {t_count:<10}")

if __name__ == "__main__":
    audit_database()

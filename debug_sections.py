from app import create_app
from app.models import db, Section, School

app = create_app()

def list_sections():
    with app.app_context():
        school = School.query.filter_by(code='SCDS').first()
        if not school:
            print("School SCDS not found.")
            return

        sections = Section.query.filter_by(school_id=school.id).all()
        print(f"Sections for {school.name} (ID: {school.id}):")
        for s in sections:
            print(f" - ID: {s.id}, Code: {s.code}, Name: {s.name}")

if __name__ == "__main__":
    list_sections()

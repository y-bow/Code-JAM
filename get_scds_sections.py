from app import create_app
from app.models import School, Section

def get_section_info():
    app = create_app()
    with app.app_context():
        scds = School.query.filter_by(code='SCDS').first()
        if not scds:
            print("Error: SCDS school not found.")
            return

        print(f"School: {scds.name} (ID: {scds.id})")
        sections = Section.query.filter_by(school_id=scds.id).all()
        for s in sections:
            print(f"- {s.name} (Code: {s.code}, ID: {s.id})")

if __name__ == "__main__":
    get_section_info()

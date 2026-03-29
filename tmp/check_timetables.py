from app import create_app
from app.models import db, Section, TimetableEntry

def check_timetables():
    app = create_app()
    with app.app_context():
        sections = Section.query.all()
        print(f"{'Section Name':<20} | {'ID':<5} | {'Entries':<10}")
        print("-" * 40)
        for s in sections:
            count = TimetableEntry.query.filter_by(section_id=s.id).count()
            print(f"{s.name:<20} | {s.id:<5} | {count:<10}")

if __name__ == "__main__":
    check_timetables()

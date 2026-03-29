from app import create_app
from app.models import db, School, Section, User, Student, Teacher

app = create_app()

def verify():
    with app.app_context():
        # Check Schools
        schools_count = School.query.count()
        print(f"Schools count: {schools_count} (Expected: 8)")
        
        # Check Sections for SCDS
        scds = School.query.filter_by(code='SCDS').first()
        if scds:
            sections_count = Section.query.filter_by(school_id=scds.id).count()
            print(f"SCDS Sections count: {sections_count} (Expected: 7)")
        else:
            print("ERROR: SCDS school not found")

        # Check Specific Users
        emails = [
            "vaibhav.b-29@scds.saiuniversity.edu.in",
            "ruddhima.p-29@scds.saiuniversity.edu.in",
            "harshitha.b-29@scds.saiuniversity.edu.in",
            "superadmin@hive.lms",
            "admin@hive.lms",
            "dean@scds.saiuniversity.edu.in"
        ]
        
        for email in emails:
            user = User.query.filter_by(email=email).first()
            if user:
                print(f"User found: {email} | Role: {user.role} | Name: {user.name}")
            else:
                print(f"ERROR: User {email} NOT found")

        # Check if Vaibhav is in Section 3
        vaibhav = User.query.filter_by(email="vaibhav.b-29@scds.saiuniversity.edu.in").first()
        if vaibhav and vaibhav.student_profile:
            section = Section.query.get(vaibhav.student_profile.section_id)
            print(f"Vaibhav Section: {section.name if section else 'None'} (Expected: Section 3)")

if __name__ == "__main__":
    verify()

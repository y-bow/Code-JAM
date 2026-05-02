import os
import sys
# Set PYTHONPATH to the current directory
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import TimetableEntry, User, Student, Announcement

app = create_app()
with app.app_context():
    # Update CGPA
    email = 'vaibhav.b-29@scds.saiuniversity.edu.in'.lower()
    user = User.query.filter(User.email.ilike(email)).first()
    if user and user.student_profile:
        user.student_profile.cgpa = 8.8
        db.session.commit()
        print(f"Updated CGPA for {user.email} to 8.8")
    
    # Check Section 3 timetable
    entries = TimetableEntry.query.filter_by(section_id=3).all()
    print(f"\nTimetable for Section 3:")
    for entry in entries:
        print(f"ID: {entry.id}, Day: {entry.day}, Title: {entry.title}, Room: {entry.room}, Status: {entry.status}")

    # Add a placeholder announcement if needed
    # (The user wants a placeholder announcement where their class has been changed)
    # I'll add one targeted to Section 3.
    # From grep earlier, I saw announcements have category='timetable', title="📚 Timetable Update", title="🚪 Room Change", etc.
    
    # I'll create a new one.
    ann = Announcement(
        school_id=1,
        section_id=3,
        teacher_id=1, # Default to admin or some teacher
        title="📚 Timetable Update",
        body="Attention Section 3: Your class schedule has been updated. Please check the timetable for recent changes in room assignments and timings.",
        category='timetable'
    )
    db.session.add(ann)
    db.session.commit()
    print("\nAdded placeholder announcement for Section 3")

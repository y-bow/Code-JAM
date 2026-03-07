from app import create_app
from flask import url_for
app = create_app()
with app.app_context():
    try:
        print(f"URL for index: {url_for('index')}")
        print(f"URL for dashboard.timetable: {url_for('dashboard.timetable')}")
        print(f"URL for dashboard.manage_timetable: {url_for('dashboard.manage_timetable')}")
        print(f"URL for messages.index: {url_for('messages.index')}")
        print("SUCCESS: All URLs built.")
    except Exception as e:
        print(f"FAILURE: {e}")

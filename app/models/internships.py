from datetime import datetime
from ._ext import db, gen_uuid


class Internship(db.Model):
    __tablename__ = 'internships'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    stipend = db.Column(db.String(100))
    application_deadline = db.Column(db.DateTime)
    description = db.Column(db.Text)
    required_skills = db.Column(db.Text)
    application_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

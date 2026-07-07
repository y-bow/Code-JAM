from datetime import datetime
from ._ext import db, gen_uuid


class LostFoundItem(db.Model):
    __tablename__ = 'lost_found_items'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    school_id = db.Column(db.String(36), db.ForeignKey('schools.id'), nullable=False)
    reporter_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    report_type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    image_path = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='open')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    reporter = db.relationship('User', backref=db.backref('lost_found_items', lazy='dynamic'))

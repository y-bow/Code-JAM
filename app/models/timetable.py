from datetime import datetime
from ._ext import db, gen_uuid


class TimetableEntry(db.Model):
    __tablename__ = 'timetable_entries'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    section_id = db.Column(db.String(36), db.ForeignKey('sections.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=True)
    day = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    teacher = db.Column(db.String(100))
    period = db.Column(db.String(50))
    room = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(50), default='var(--primary-color)')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    section = db.relationship('Section', backref=db.backref('timetable_entries', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('timetable_entries', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_timetable_section', 'section_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'day': self.day,
            'startTime': self.start_time,
            'endTime': self.end_time,
            'title': self.title,
            'subject': self.title,
            'teacher': self.teacher or '',
            'period': self.period or '',
            'room': self.room,
            'color': self.color,
            'status': self.status,
            'course_id': self.course_id,
        }

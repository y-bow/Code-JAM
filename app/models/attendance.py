from datetime import datetime
from ._ext import db, gen_uuid


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)

    course = db.relationship('Course', backref=db.backref('attendance_records', lazy='dynamic'))
    student = db.relationship('User', backref=db.backref('attendance_records', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', 'date', name='uq_attendance_record'),
        db.Index('ix_attendance_course_date', 'course_id', 'date'),
        db.Index('ix_attendance_student', 'student_id'),
    )

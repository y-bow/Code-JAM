from datetime import datetime
from ._ext import db, gen_uuid


class TeacherTodo(db.Model):
    __tablename__ = 'teacher_todos'
    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    teacher_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TeacherRating(db.Model):
    __tablename__ = 'teacher_ratings'
    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CustomTask(db.Model):
    __tablename__ = 'custom_tasks'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('custom_tasks', lazy='dynamic'))

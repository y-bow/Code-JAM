import re
from datetime import datetime
from ._ext import db, bcrypt, gen_uuid

ROLE_HIERARCHY = {
    'student': 1,
    'class_rep': 2,
    'assistant_professor': 3,
    'professor': 4,
    'dean': 5,
    'admin': 99,
    'superadmin': 100,
}

VALID_ROLES = {'student', 'class_rep', 'assistant_professor', 'professor', 'dean', 'admin', 'superadmin'}


def generate_username(email, institution_id=None):
    prefix = email.split('@')[0].lower()
    prefix = re.sub(r'[^a-z0-9._-]', '', prefix)[:50]
    if not prefix:
        prefix = 'user'
    username = prefix
    query = User.query.filter_by(username=username)
    if institution_id:
        query = query.filter_by(institution_id=institution_id)
    suffix = 1
    while query.first() is not None:
        username = f'{prefix}{suffix}'
        suffix += 1
        query = User.query.filter_by(username=username)
        if institution_id:
            query = query.filter_by(institution_id=institution_id)
    return username


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    institution_id = db.Column(db.String(36), db.ForeignKey('institutions.id'), nullable=True)
    username = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('institution_id', 'email', name='uq_user_institution_email'),
        db.Index('ix_user_institution', 'institution_id'),
        db.Index('ix_user_role', 'institution_id', 'role'),
        db.Index('ix_user_username', 'username'),
    )

    @property
    def role_level(self):
        return ROLE_HIERARCHY.get(self.role, -1)

    def has_minimum_role(self, min_role):
        return self.role_level >= ROLE_HIERARCHY.get(min_role, 999)

    def __repr__(self):
        return f'<User {self.email} ({self.role}) @ Institution {self.institution_id}>'


class Student(db.Model):
    __tablename__ = 'students'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    section_id = db.Column(db.String(36), db.ForeignKey('sections.id'), nullable=False)
    enrollment_year = db.Column(db.Integer, nullable=False)
    major = db.Column(db.String(100))
    sgpa = db.Column(db.Float, default=0.0)
    cgpa = db.Column(db.Float, default=0.0)
    lab_section = db.Column(db.Integer, nullable=True)

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    section = db.relationship('Section', backref=db.backref('students', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_student_section', 'section_id'),
    )


class Teacher(db.Model):
    __tablename__ = 'teachers'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    department = db.Column(db.String(100))
    office_hours = db.Column(db.String(200))

    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))

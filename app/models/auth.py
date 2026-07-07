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


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    school_id = db.Column(db.String(36), db.ForeignKey('schools.id'), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('school_id', 'email', name='uq_user_school_email'),
        db.Index('ix_user_school', 'school_id'),
        db.Index('ix_user_role', 'school_id', 'role'),
    )

    @property
    def role_level(self):
        return ROLE_HIERARCHY.get(self.role, -1)

    def has_minimum_role(self, min_role):
        return self.role_level >= ROLE_HIERARCHY.get(min_role, 999)

    def __repr__(self):
        return f'<User {self.email} ({self.role}) @ School {self.school_id}>'


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

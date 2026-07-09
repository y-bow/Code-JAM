from datetime import datetime
from ._ext import db, gen_uuid


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    section_id = db.Column(db.String(36), db.ForeignKey('sections.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    max_students = db.Column(db.Integer, default=50)
    meet_link = db.Column(db.String(500), nullable=True)

    teacher = db.relationship('User', backref=db.backref('taught_courses', lazy='dynamic'))
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic',
                                  cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic',
                                  cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='course', lazy='dynamic',
                              cascade='all, delete-orphan')
    resources = db.relationship('Resource', backref='course', lazy='dynamic',
                                cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('section_id', 'code', name='uq_course_section_code'),
        db.Index('ix_course_section', 'section_id'),
        db.Index('ix_course_teacher', 'teacher_id'),
    )

    @property
    def institution_id(self):
        return self.section.institution_id if self.section else None


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), primary_key=True)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

    student = db.relationship('User', backref=db.backref('enrollments', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_enrollment_student', 'student_id'),
        db.Index('ix_enrollment_course', 'course_id'),
    )

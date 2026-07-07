from datetime import datetime
from ._ext import db, gen_uuid


class Club(db.Model):
    __tablename__ = 'clubs'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    school_id = db.Column(db.String(36), db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('school_id', 'name', name='uq_club_school_name'),
        db.Index('ix_club_school', 'school_id'),
    )

    school = db.relationship('School', backref=db.backref('clubs', lazy='dynamic'))


class ExternalEvent(db.Model):
    __tablename__ = 'external_events'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    school_id = db.Column(db.String(36), db.ForeignKey('schools.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    hosting_college = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    registration_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_event_school', 'school_id'),
    )

    school = db.relationship('School', backref=db.backref('external_events', lazy='dynamic'))


class ProfessorAssistant(db.Model):
    __tablename__ = 'professor_assistants'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    professor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    assistant_teacher_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    course = db.relationship('Course', backref=db.backref('professor_assistants', cascade='all, delete-orphan'))
    professor = db.relationship('User', foreign_keys=[professor_id])
    assistant = db.relationship('User', foreign_keys=[assistant_teacher_id],
                                backref=db.backref('assistant_roles', lazy='dynamic'))


class ClassRepNomination(db.Model):
    __tablename__ = 'class_rep_nominations'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    section_id = db.Column(db.String(36), db.ForeignKey('sections.id'), nullable=False)
    nominated_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')
    nominated_at = db.Column(db.DateTime, default=datetime.utcnow)
    decided_at = db.Column(db.DateTime)

    student = db.relationship('User', foreign_keys=[student_id])
    nominator = db.relationship('User', foreign_keys=[nominated_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    course = db.relationship('Course')
    section = db.relationship('Section')

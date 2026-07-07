from datetime import datetime
from ._ext import db, gen_uuid


class School(db.Model):
    __tablename__ = 'schools'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    domain = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sections = db.relationship('Section', backref='school', lazy='dynamic',
                               cascade='all, delete-orphan')
    users = db.relationship('User', backref='school', lazy='dynamic',
                            cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='school', lazy='dynamic',
                                    cascade='all, delete-orphan')

    def __repr__(self):
        return f'<School {self.code}: {self.name}>'


Institution = School


class Section(db.Model):
    __tablename__ = 'sections'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    school_id = db.Column(db.String(36), db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('school_id', 'code', name='uq_section_school_code'),
        db.Index('ix_section_school', 'school_id'),
    )

    courses = db.relationship('Course', backref='section', lazy='dynamic',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Section {self.code} @ School {self.school_id}>'


class AcademicYear(db.Model):
    __tablename__ = 'academic_years'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    institution_id = db.Column(db.String(36), db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    institution = db.relationship(School, backref=db.backref('academic_years', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('institution_id', 'name', name='uq_academic_year_name'),
        db.Index('ix_academic_year_institution', 'institution_id'),
    )

    def __repr__(self):
        return f'<AcademicYear {self.name} @ Institution {self.institution_id}>'

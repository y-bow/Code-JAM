from datetime import datetime
from app.models._ext import db, gen_uuid


class Institution(db.Model):
    __tablename__ = 'institutions'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    domain = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    has_academic_units = db.Column(db.Boolean, default=False)
    academic_unit_label = db.Column(db.String(50), default='School')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    departments = db.relationship('Department', backref='institution', lazy='dynamic',
                                  cascade='all, delete-orphan',
                                  foreign_keys='Department.institution_id')
    sections = db.relationship('Section', backref='institution', lazy='dynamic',
                                cascade='all, delete-orphan',
                                foreign_keys='Section.institution_id')
    users = db.relationship('User', backref='institution', lazy='dynamic',
                            cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='institution', lazy='dynamic',
                                    cascade='all, delete-orphan')
    academic_years = db.relationship('AcademicYear', backref='institution', lazy='dynamic',
                                     cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Institution {self.code}: {self.name}>'


School = Institution


class AcademicUnit(db.Model):
    __tablename__ = 'academic_units'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    institution_id = db.Column(db.String(36), db.ForeignKey('institutions.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    departments = db.relationship('Department', backref='academic_unit', lazy='dynamic',
                                  cascade='all, delete-orphan')

    institution = db.relationship('Institution', backref=db.backref('academic_units', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('institution_id', 'code', name='uq_academic_unit_institution_code'),
        db.Index('ix_academic_unit_institution', 'institution_id'),
    )

    def __repr__(self):
        return f'<AcademicUnit {self.code}: {self.name}>'


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    institution_id = db.Column(db.String(36), db.ForeignKey('institutions.id'), nullable=False)
    academic_unit_id = db.Column(db.String(36), db.ForeignKey('academic_units.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    programs = db.relationship('Program', backref='department', lazy='dynamic',
                               cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('institution_id', 'code', name='uq_department_institution_code'),
        db.Index('ix_department_institution', 'institution_id'),
        db.Index('ix_department_academic_unit', 'academic_unit_id'),
    )

    def __repr__(self):
        return f'<Department {self.code}: {self.name}>'


class Program(db.Model):
    __tablename__ = 'programs'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    department_id = db.Column(db.String(36), db.ForeignKey('departments.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    duration_years = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sections = db.relationship('Section', backref='program', lazy='dynamic',
                               cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('department_id', 'code', name='uq_program_department_code'),
        db.Index('ix_program_department', 'department_id'),
    )

    def __repr__(self):
        return f'<Program {self.code}: {self.name}>'


class Section(db.Model):
    __tablename__ = 'sections'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    institution_id = db.Column(db.String(36), db.ForeignKey('institutions.id'), nullable=False)
    program_id = db.Column(db.String(36), db.ForeignKey('programs.id'), nullable=False)
    department_id = db.Column(db.String(36), db.ForeignKey('departments.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('program_id', 'code', name='uq_section_program_code'),
        db.Index('ix_section_institution', 'institution_id'),
        db.Index('ix_section_program', 'program_id'),
        db.Index('ix_section_department', 'department_id'),
    )



    def __repr__(self):
        return f'<Section {self.code} @ Institution {self.institution_id}>'


class AcademicYear(db.Model):
    __tablename__ = 'academic_years'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    institution_id = db.Column(db.String(36), db.ForeignKey('institutions.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('institution_id', 'name', name='uq_academic_year_name'),
        db.Index('ix_academic_year_institution', 'institution_id'),
    )

    def __repr__(self):
        return f'<AcademicYear {self.name}>'

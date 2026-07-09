from ..models import db, User, Institution, Department, Section, AcademicYear, SiteSetting, get_setting, set_setting
from ..models._ext import bcrypt
from ..models.auth import generate_username


SETUP_COMPLETE_KEY = 'system.setup_complete'


def is_setup_complete():
    return get_setting(SETUP_COMPLETE_KEY, False) is True


def has_admin_users():
    return User.query.filter_by(role='admin').count() > 0


def has_any_institutions():
    return Institution.query.count() > 0


def create_admin_account(name, email, password):
    existing = User.query.filter_by(role='admin').first()
    if existing:
        return existing, None

    if User.query.filter_by(email=email).first():
        return None, 'Email already in use'

    cleaned_email = email.strip().lower()
    user = User(
        email=cleaned_email,
        username=generate_username(cleaned_email),
        password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
        role='admin',
        name=name.strip(),
    )
    db.session.add(user)
    db.session.commit()
    return user, None


def create_institution(name, code):
    existing = Institution.query.first()
    if existing:
        return existing, None

    institution = Institution(name=name.strip(), code=code.strip().upper())
    db.session.add(institution)
    db.session.commit()
    return institution, None


def create_academic_year(name, start_date, end_date, institution_id):
    existing = AcademicYear.query.filter_by(institution_id=institution_id, name=name).first()
    if existing:
        return existing, None
    if not start_date or not end_date:
        return None, 'Start date and end date are required'
    try:
        from datetime import datetime as dt
        start = dt.strptime(start_date, '%Y-%m-%d').date()
        end = dt.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return None, 'Invalid date format. Use YYYY-MM-DD.'
    year = AcademicYear(
        institution_id=institution_id,
        name=name.strip(),
        start_date=start,
        end_date=end,
        is_current=True,
    )
    db.session.add(year)
    db.session.commit()
    return year, None


def create_department(name, code, institution_id):
    existing = Department.query.filter_by(institution_id=institution_id, code=code).first()
    if existing:
        return existing, None
    dept = Department(institution_id=institution_id, name=name.strip(), code=code.strip().upper())
    db.session.add(dept)
    db.session.commit()
    return dept, None


def create_section(name, code, department_id, batch_year, institution_id, program_id=None):
    existing = Section.query.filter_by(institution_id=institution_id, code=code).first()
    if existing:
        return existing, None
    try:
        by = int(batch_year)
    except (ValueError, TypeError):
        by = datetime.utcnow().year
    section = Section(
        institution_id=institution_id,
        program_id=program_id or department_id,
        department_id=department_id,
        name=name.strip(),
        code=code.strip().upper(),
        batch_year=by,
    )
    db.session.add(section)
    db.session.commit()
    return section, None


def save_theme_settings(primary_color, theme_mode):
    set_setting('theme.primary_color', primary_color, 'string', 'theme', 'Primary accent color')
    set_setting('theme.active', theme_mode, 'string', 'theme', 'Default theme mode')
    set_setting('theme.setup_completed', 'true', 'string', 'theme', 'Theme configured during setup')


def mark_setup_complete():
    set_setting(SETUP_COMPLETE_KEY, True, 'bool', 'system', 'Whether initial setup wizard has been completed')

from ..models import db, User, School, SiteSetting, get_setting, set_setting
from ..models._ext import bcrypt


SETUP_COMPLETE_KEY = 'system.setup_complete'


def is_setup_complete():
    if get_setting(SETUP_COMPLETE_KEY, False):
        return True
    if has_admin_users() and has_any_schools():
        return True
    return False


def has_admin_users():
    return User.query.filter_by(role='admin').count() > 0


def has_any_schools():
    return School.query.count() > 0


def create_admin_account(name, email, password):
    existing = User.query.filter_by(role='admin').first()
    if existing:
        return existing, None

    if User.query.filter_by(email=email).first():
        return None, 'Email already in use'

    user = User(
        email=email.strip().lower(),
        password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
        role='admin',
        name=name.strip(),
    )
    db.session.add(user)
    db.session.commit()
    return user, None


def create_institution(name, code):
    existing = School.query.first()
    if existing:
        return existing, None

    school = School(name=name.strip(), code=code.strip().upper())
    db.session.add(school)
    db.session.commit()
    return school, None


def save_theme_settings(primary_color, theme_mode):
    set_setting('theme.primary_color', primary_color, 'string', 'theme', 'Primary accent color')
    set_setting('theme.default_mode', theme_mode, 'string', 'theme', 'Default theme mode')
    set_setting('theme.setup_completed', 'true', 'string', 'theme', 'Theme configured during setup')


def mark_setup_complete():
    set_setting(SETUP_COMPLETE_KEY, True, 'bool', 'system', 'Whether initial setup wizard has been completed')

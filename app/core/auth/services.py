import re
from app.models import User, bcrypt


def authenticate(email, password):
    user = User.query.filter_by(email=email.strip().lower()).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        return user
    return None


def validate_password_strength(password):
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long.')
    if not re.search(r"[A-Z]", password):
        errors.append('Password must contain at least one uppercase letter.')
    if not re.search(r"[0-9]", password):
        errors.append('Password must contain at least one number.')
    if not re.search(r"[!@#$%^&*]", password):
        errors.append('Password must contain at least one special character (!@#$%^&*).')
    return errors


def change_user_password(user, current_password, new_password, confirm_password):
    if not bcrypt.check_password_hash(user.password_hash, current_password):
        return False, 'Current password is incorrect.'
    if current_password == new_password:
        return False, 'New password must be different from current password.'
    if new_password != confirm_password:
        return False, 'New password and confirmation do not match.'
    pw_errors = validate_password_strength(new_password)
    if pw_errors:
        return False, pw_errors[0]
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.must_change_password = False
    from app.models import db
    db.session.commit()
    return True, 'Password updated successfully.'


def get_redirect_target(user):
    role = user.role
    if role in ('student', 'class_rep'):
        return 'dashboard.student_dashboard'
    elif role in ('professor', 'assistant_professor'):
        return 'dashboard.teacher_dashboard'
    elif role == 'admin':
        return 'dashboard.admin_dashboard'
    elif role == 'dean':
        return 'dashboard.school_analytics'
    return 'index'

from functools import wraps
from flask import session, g, abort, flash, redirect, url_for
from app.models import User, ROLE_HIERARCHY, Announcement


def tenant_scoped(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        user = User.query.get(user_id)
        if not user or not user.is_active:
            session.clear()
            flash('Account not found or deactivated.', 'danger')
            return redirect(url_for('auth.login'))

        if user.role not in ('admin', 'superadmin'):
            if not user.institution or not user.institution.is_active:
                session.clear()
                flash('Your institution is currently inactive.', 'danger')
                return redirect(url_for('auth.login'))

        g.current_user = user
        g.institution_id = user.institution_id

        if user.role == 'admin':
            g.recent_announcements = Announcement.query.order_by(Announcement.posted_at.desc()).limit(3).all()
        else:
            g.recent_announcements = Announcement.query.filter_by(institution_id=user.institution_id).order_by(Announcement.posted_at.desc()).limit(3).all()

        return f(*args, **kwargs)
    return decorated_function


def role_minimum(min_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user:
                abort(401)

            required_level = ROLE_HIERARCHY.get(min_role)
            if required_level is None:
                raise ValueError(f"Unknown role: {min_role}")

            if user.role_level < required_level:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def owns_resource(resource_obj, institution_id_attr='institution_id'):
    if resource_obj is None:
        abort(404)

    obj_institution_id = getattr(resource_obj, institution_id_attr, None)
    if obj_institution_id is None:
        abort(404)

    if g.current_user.role == 'admin':
        return

    if obj_institution_id != g.institution_id:
        abort(403)

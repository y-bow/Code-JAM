from functools import wraps
from flask import session, g, abort, flash, redirect, url_for
from app.models import User, ROLE_HIERARCHY, Message, Announcement


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
            if not user.school or not user.school.is_active:
                session.clear()
                flash('Your institution is currently inactive.', 'danger')
                return redirect(url_for('auth.login'))

        g.current_user = user
        g.institution_id = user.school_id
        g.school_id = user.school_id

        g.unread_messages = Message.query.filter_by(recipient_id=user.id, is_read=False).order_by(Message.sent_at.desc()).limit(5).all()
        g.unread_count = Message.query.filter_by(recipient_id=user.id, is_read=False).count()

        if user.role == 'admin':
            g.recent_announcements = Announcement.query.order_by(Announcement.posted_at.desc()).limit(3).all()
        else:
            g.recent_announcements = Announcement.query.filter_by(school_id=user.school_id).order_by(Announcement.posted_at.desc()).limit(3).all()

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


def owns_resource(resource_obj, school_id_attr='school_id'):
    if resource_obj is None:
        abort(404)

    obj_school_id = getattr(resource_obj, school_id_attr, None)
    if obj_school_id is None:
        abort(404)

    if g.current_user.role == 'admin':
        return

    if obj_school_id != g.school_id:
        abort(403)

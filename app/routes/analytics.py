from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort
from ..middleware import institution_scoped, role_minimum
from ..services import (
    get_institution_stats,
    get_at_risk_students,
    get_teacher_ratings_data,
    get_pending_nominations,
    process_nomination,
)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics',
                          template_folder='templates/analytics')


@analytics_bp.route('/')
@institution_scoped
@role_minimum('dean')
def institution_analytics():
    stats = get_institution_stats(g.institution_id)
    return render_template('analytics.html', **stats)


@analytics_bp.route('/early-warning')
@institution_scoped
@role_minimum('dean')
def early_warning():
    at_risk_students = get_at_risk_students(g.institution_id)
    return render_template('early_warning.html', at_risk_students=at_risk_students)


@analytics_bp.route('/dean/ratings')
@institution_scoped
@role_minimum('dean')
def dean_ratings():
    teacher_stats = get_teacher_ratings_data(g.institution_id)
    return render_template('dean_ratings.html', teacher_stats=teacher_stats)


@analytics_bp.route('/dean/nominations')
@institution_scoped
@role_minimum('dean')
def dean_nominations():
    nominations = get_pending_nominations(g.institution_id)
    return render_template('dean_nominations.html', nominations=nominations)


@analytics_bp.route('/dean/nominations/<string:nom_id>/<action>', methods=['POST'])
@institution_scoped
@role_minimum('dean')
def handle_nomination(nom_id, action):
    success, message = process_nomination(nom_id, action, g.institution_id, g.current_user.id)
    if not success and message == "Unauthorized":
        abort(403)
    flash(message, 'success' if success else 'info')
    return redirect(url_for('analytics.dean_nominations'))

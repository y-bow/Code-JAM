from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort
from datetime import datetime
from ..middleware import school_scoped, role_minimum
from ..models import (
    db, User, Student, Section, Course, Attendance,
    TeacherRating, ClassRepNomination, get_setting
)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/')
@school_scoped
@role_minimum('dean')
def school_analytics():
    total_students = User.query.filter_by(school_id=g.school_id, role='student').count()
    total_teachers = User.query.filter_by(school_id=g.school_id, role='teacher').count()
    total_sections = Section.query.filter_by(school_id=g.school_id).count()
    total_courses = (
        Course.query
        .join(Section)
        .filter(Section.school_id == g.school_id)
        .count()
    )

    avg_attendance_raw = db.session.query(db.func.avg(Attendance.status == 'present')).filter(
        User.school_id == g.school_id, User.role == 'student'
    ).join(User, Attendance.student_id == User.id).scalar()
    avg_attendance = round(float(avg_attendance_raw) * 100, 1) if avg_attendance_raw is not None else 0.0

    avg_cgpa_raw = db.session.query(db.func.avg(Student.cgpa)).join(User).filter(
        User.school_id == g.school_id
    ).scalar()
    avg_cgpa = round(float(avg_cgpa_raw), 2) if avg_cgpa_raw is not None else 0.0

    return render_template('dashboard/analytics.html',
                           total_students=total_students,
                           total_teachers=total_teachers,
                           total_sections=total_sections,
                           total_courses=total_courses,
                           avg_attendance=avg_attendance,
                           avg_cgpa=avg_cgpa)


@analytics_bp.route('/early-warning')
@school_scoped
@role_minimum('dean')
def early_warning():
    cgpa_threshold = get_setting('early_warning.cgpa_threshold', 1.5)
    at_risk_students = []

    low_cgpa_students = Student.query.join(User).filter(
        User.school_id == g.school_id,
        Student.cgpa < cgpa_threshold
    ).all()

    for s in low_cgpa_students:
        at_risk_students.append({
            'user': s.user,
            'reason': 'Low CGPA',
            'value': f"{s.cgpa:.2f}"
        })

    return render_template('dashboard/early_warning.html', at_risk_students=at_risk_students)


@analytics_bp.route('/dean/ratings')
@school_scoped
@role_minimum('dean')
def dean_ratings():
    teachers = User.query.filter_by(school_id=g.school_id, role='teacher').all()

    teacher_stats = []
    for t in teachers:
        avg_rating = db.session.query(db.func.avg(TeacherRating.rating)).filter_by(teacher_id=t.id).scalar() or 0
        total_ratings = TeacherRating.query.filter_by(teacher_id=t.id).count()
        teacher_stats.append({
            'id': t.id,
            'name': t.name,
            'avg_rating': round(float(avg_rating), 1) if avg_rating else 0.0,
            'total_ratings': total_ratings,
            'recent_reviews': TeacherRating.query.filter_by(teacher_id=t.id).order_by(TeacherRating.created_at.desc()).limit(3).all()
        })

    return render_template('dashboard/dean_ratings.html', teacher_stats=teacher_stats)


@analytics_bp.route('/dean/nominations')
@school_scoped
@role_minimum('dean')
def dean_nominations():
    nominations = ClassRepNomination.query.join(Section).filter(
        Section.school_id == g.school_id,
        ClassRepNomination.status == 'pending'
    ).all()
    return render_template('dashboard/dean_nominations.html', nominations=nominations)


@analytics_bp.route('/dean/nominations/<string:nom_id>/<action>', methods=['POST'])
@school_scoped
@role_minimum('dean')
def handle_nomination(nom_id, action):
    nom = ClassRepNomination.query.get_or_404(nom_id)
    if nom.section.school_id != g.school_id:
        abort(403)

    if action == 'approve':
        nom.status = 'approved'
        nom.approved_by = g.current_user.id
        nom.decided_at = datetime.utcnow()
        student = User.query.get(nom.student_id)
        student.role = 'class_rep'
        flash(f'Class Rep nomination for {student.name} approved.', 'success')
    elif action == 'reject':
        nom.status = 'rejected'
        nom.approved_by = g.current_user.id
        nom.decided_at = datetime.utcnow()
        flash('Class Rep nomination rejected.', 'info')

    db.session.commit()
    return redirect(url_for('analytics.dean_nominations'))

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, g, flash
from ..middleware import school_scoped, role_minimum
from ..models import db, Grade, Attendance, Enrollment, Assignment, Submission
from ..services import (
    get_student_today_classes,
    get_assigned_courses,
    get_teacher_today_classes,
    get_teacher_stats,
    get_teacher_graphs,
    get_teacher_tasks,
    get_user_courses,
    update_meet_link,
)

academics_bp = Blueprint('academics', __name__, url_prefix='/academics',
                          template_folder='templates/academics')


@academics_bp.route('/student')
@school_scoped
def student_dashboard():
    user = g.current_user
    today_classes = get_student_today_classes(user.student_profile)

    total_attendance = Attendance.query.filter_by(student_id=user.id).count()
    present_attendance = Attendance.query.filter_by(student_id=user.id, status='present').count()
    attendance_pct = round((present_attendance / total_attendance * 100)) if total_attendance > 0 else None

    enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=user.id).all()]
    courses_count = len(enrolled_course_ids)

    pending_count = Assignment.query.filter(
        Assignment.course_id.in_(enrolled_course_ids),
        ~Assignment.submissions.any(Submission.student_id == user.id)
    ).count() if enrolled_course_ids else 0

    upcoming_deadlines = Assignment.query.filter(
        Assignment.course_id.in_(enrolled_course_ids),
        Assignment.due_date >= datetime.utcnow()
    ).order_by(Assignment.due_date).limit(5).all() if enrolled_course_ids else []

    return render_template('student_dashboard.html',
                           today_classes=today_classes,
                           attendance_pct=attendance_pct,
                           courses_count=courses_count,
                           pending_count=pending_count,
                           upcoming_deadlines=upcoming_deadlines)


@academics_bp.route('/teacher')
@school_scoped
@role_minimum('assistant_professor')
def teacher_dashboard():
    user = g.current_user
    assigned_courses = get_assigned_courses(user)
    today_classes = get_teacher_today_classes(user, assigned_courses)
    tasks = get_teacher_tasks(user.id)
    stats, recent_reviews = get_teacher_stats(user, assigned_courses)
    graphs_json = get_teacher_graphs(assigned_courses)

    return render_template('teacher_dashboard.html',
                           today_classes=today_classes,
                           tasks=tasks,
                           stats=stats,
                           reviews=recent_reviews,
                           graphs=graphs_json)


@academics_bp.route('/my-courses')
@school_scoped
def my_courses():
    courses = get_user_courses(g.current_user, g.school_id)
    return render_template('courses.html', courses=courses)


@academics_bp.route('/grades')
@school_scoped
def grades():
    user = g.current_user
    if user.role in ('student', 'class_rep'):
        grades = Grade.query.filter_by(student_id=user.id).order_by(Grade.calculated_at.desc()).all()
    else:
        grades = []
    return render_template('grades.html', grades=grades)


@academics_bp.route('/update_meet', methods=['POST'])
@school_scoped
@role_minimum('professor')
def update_meet_link_route():
    course_id = request.form.get('course_id')
    meet_link = request.form.get('meet_link')
    if update_meet_link(course_id, meet_link, g.current_user.id):
        flash('Meeting link updated successfully.', 'success')
    return redirect(url_for('academics.teacher_dashboard'))

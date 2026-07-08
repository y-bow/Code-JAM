from flask import Blueprint, render_template, request, redirect, url_for, g, flash
from ..middleware import school_scoped, role_minimum
from ..models import db
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

academics_bp = Blueprint('academics', __name__, url_prefix='/academics')


@academics_bp.route('/student')
@school_scoped
def student_dashboard():
    today_classes = get_student_today_classes(g.current_user.student_profile)
    return render_template('dashboard/student_dashboard.html', today_classes=today_classes)


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

    return render_template('dashboard/teacher_dashboard.html',
                           today_classes=today_classes,
                           tasks=tasks,
                           stats=stats,
                           reviews=recent_reviews,
                           graphs=graphs_json)


@academics_bp.route('/my-courses')
@school_scoped
def my_courses():
    courses = get_user_courses(g.current_user, g.school_id)
    return render_template('dashboard/courses.html', courses=courses)


@academics_bp.route('/grades')
@school_scoped
def grades():
    return render_template('dashboard/grades.html')


@academics_bp.route('/update_meet', methods=['POST'])
@school_scoped
@role_minimum('professor')
def update_meet_link_route():
    course_id = request.form.get('course_id')
    meet_link = request.form.get('meet_link')
    if update_meet_link(course_id, meet_link, g.current_user.id):
        flash('Meeting link updated successfully.', 'success')
    return redirect(url_for('academics.teacher_dashboard'))

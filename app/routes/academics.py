from flask import Blueprint, render_template, session, request, redirect, url_for, g, flash
from datetime import datetime
from ..middleware import school_scoped, role_minimum
from ..models import (
    db, User, Student, Course, Enrollment, Section, Announcement,
    TimetableEntry, TeacherRating, Attendance, Grade, TeacherTodo,
    ProfessorAssistant
)
import pandas as pd
import plotly.express as px
import plotly.utils
import json

academics_bp = Blueprint('academics', __name__, url_prefix='/academics')


@academics_bp.route('/student')
@school_scoped
def student_dashboard():
    user = g.current_user
    today_classes = []

    current_day = datetime.now().weekday()
    if current_day <= 4:
        if user.student_profile and user.student_profile.section_id:
            entries_query = TimetableEntry.query.filter_by(
                section_id=user.student_profile.section_id,
                day=current_day
            )
            student_lab_section = user.student_profile.lab_section
            section_theory_num = user.student_profile.section_id
            entries = [
                e for e in entries_query.all()
                if student_lab_section is None
                or '(LAB)' not in e.title
                or student_lab_section == 3
            ]

            today_classes = [entry.to_dict() for entry in entries]
            today_classes.sort(key=lambda x: datetime.strptime(x['startTime'].replace(" ", "").upper(), '%I:%M%p').time() if 'AM' in x['startTime'].upper() or 'PM' in x['startTime'].upper() else x['startTime'])

    return render_template('dashboard/student_dashboard.html', today_classes=today_classes)


@academics_bp.route('/teacher')
@school_scoped
@role_minimum('assistant_professor')
def teacher_dashboard():
    user = g.current_user
    import plotly.utils
    import json

    if user.role == 'assistant_professor':
        assigned_courses = Course.query.join(ProfessorAssistant).filter(
            ProfessorAssistant.assistant_teacher_id == user.id,
            ProfessorAssistant.is_active == True
        ).all()
    else:
        assigned_courses = Course.query.filter_by(teacher_id=user.id).all()

    assigned_course_ids = [c.id for c in assigned_courses]

    current_day = datetime.now().weekday()
    today_classes = []
    if current_day <= 4:
        entries = (
            TimetableEntry.query
            .filter(TimetableEntry.course_id.in_(assigned_course_ids))
            .filter_by(day=current_day)
            .order_by(TimetableEntry.start_time)
            .all()
        )

        for entry in entries:
            course = next((c for c in assigned_courses if c.name == entry.title), None)
            student_count = course.enrollments.count() if course else 0
            d = entry.to_dict()
            d['studentCount'] = student_count
            today_classes.append(d)

        today_classes.sort(key=lambda x: datetime.strptime(x['startTime'].replace(" ", "").upper(), '%I:%M%p').time() if 'AM' in x['startTime'].upper() or 'PM' in x['startTime'].upper() else x['startTime'])

    tasks = TeacherTodo.query.filter_by(teacher_id=user.id).order_by(TeacherTodo.is_completed, TeacherTodo.created_at.desc()).all()

    total_students = db.session.query(db.func.count(db.distinct(Enrollment.student_id))).filter(Enrollment.course_id.in_(assigned_course_ids)).scalar() or 0
    managed_courses_count = len(assigned_courses)

    avg_rating = db.session.query(db.func.avg(TeacherRating.rating)).filter_by(teacher_id=user.id).scalar() or 0
    total_ratings = TeacherRating.query.filter_by(teacher_id=user.id).count()
    recent_reviews = TeacherRating.query.filter_by(teacher_id=user.id).order_by(TeacherRating.created_at.desc()).limit(5).all()

    graphs_json = {}

    grade_data = []
    for course in assigned_courses:
        avg_grade = db.session.query(db.func.avg(Grade.grade)).filter_by(course_id=course.id).scalar() or 0
        grade_data.append({'Course': course.code, 'Avg Grade': round(avg_grade, 2)})

    if grade_data:
        df_grades = pd.DataFrame(grade_data)
        fig_grades = px.bar(df_grades, x='Course', y='Avg Grade', title='Avg Grade per Class', template='plotly_dark')
        fig_grades.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        graphs_json['grades'] = json.dumps(fig_grades, cls=plotly.utils.PlotlyJSONEncoder)

    att_data = db.session.query(Attendance.status, db.func.count(Attendance.id)).filter(Attendance.course_id.in_(assigned_course_ids)).group_by(Attendance.status).all()
    if att_data:
        df_att = pd.DataFrame(att_data, columns=['Status', 'Count'])
        fig_att = px.pie(df_att, values='Count', names='Status', title='Attendance Distribution', template='plotly_dark')
        fig_att.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        graphs_json['attendance'] = json.dumps(fig_att, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('dashboard/teacher_dashboard.html',
                           today_classes=today_classes,
                           tasks=tasks,
                           stats={
                               'students': total_students,
                               'courses': managed_courses_count,
                               'rating': round(float(avg_rating), 1),
                               'rating_count': total_ratings
                           },
                            reviews=recent_reviews,
                            graphs=graphs_json)


@academics_bp.route('/my-courses')
@school_scoped
def my_courses():
    user = g.current_user

    if user.role in ('student', 'class_rep'):
        courses = (
            Course.query
            .join(Enrollment, Enrollment.course_id == Course.id)
            .join(Section, Course.section_id == Section.id)
            .filter(
                Enrollment.student_id == user.id,
                Section.school_id == g.school_id
            )
            .all()
        )
    elif user.role == 'professor':
        courses = (
            Course.query
            .join(Section)
            .filter(
                Course.teacher_id == user.id,
                Section.school_id == g.school_id
            )
            .all()
        )
    elif user.role == 'assistant_professor':
        courses = (
            Course.query
            .join(ProfessorAssistant, ProfessorAssistant.course_id == Course.id)
            .filter(
                ProfessorAssistant.assistant_teacher_id == user.id,
                ProfessorAssistant.is_active == True
            )
            .all()
        )
    elif user.role in ('dean', 'timetable_manager'):
        courses = (
            Course.query
            .join(Section)
            .filter(Section.school_id == g.school_id)
            .all()
        )
    else:
        courses = []

    return render_template('dashboard/courses.html', courses=courses)


@academics_bp.route('/grades')
@school_scoped
def grades():
    return render_template('dashboard/grades.html')


@academics_bp.route('/update_meet', methods=['POST'])
@school_scoped
@role_minimum('professor')
def update_meet_link():
    course_id = request.form.get('course_id')
    meet_link = request.form.get('meet_link')
    course = Course.query.get_or_404(course_id)
    if course.teacher_id == g.current_user.id:
        course.meet_link = meet_link
        db.session.commit()
        flash('Meeting link updated successfully.', 'success')
    return redirect(url_for('academics.teacher_dashboard'))

from datetime import datetime
from ..models import (
    db, User, Student, Course, Enrollment, Section,
    TimetableEntry, TeacherRating, Attendance, Grade,
    TeacherTodo, ProfessorAssistant
)
import pandas as pd
import plotly.express as px
import plotly.utils
import json


def get_student_today_classes(student_profile):
    today_classes = []
    current_day = datetime.now().weekday()
    if current_day > 4:
        return today_classes

    if not student_profile or not student_profile.section_id:
        return today_classes

    entries_query = TimetableEntry.query.filter_by(
        section_id=student_profile.section_id,
        day=current_day
    )
    student_lab_section = student_profile.lab_section
    entries = [
        e for e in entries_query.all()
        if student_lab_section is None
        or '(LAB)' not in e.title
        or student_lab_section == 3
    ]

    today_classes = [entry.to_dict() for entry in entries]
    today_classes.sort(
        key=lambda x: datetime.strptime(
            x['startTime'].replace(" ", "").upper(), '%I:%M%p'
        ).time() if 'AM' in x['startTime'].upper() or 'PM' in x['startTime'].upper() else x['startTime']
    )
    return today_classes


def get_assigned_courses(user):
    if user.role == 'assistant_professor':
        return Course.query.join(ProfessorAssistant).filter(
            ProfessorAssistant.assistant_teacher_id == user.id,
            ProfessorAssistant.is_active == True
        ).all()
    return Course.query.filter_by(teacher_id=user.id).all()


def get_teacher_today_classes(user, assigned_courses):
    assigned_course_ids = [c.id for c in assigned_courses]
    today_classes = []
    current_day = datetime.now().weekday()
    if current_day > 4:
        return today_classes

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

    today_classes.sort(
        key=lambda x: datetime.strptime(
            x['startTime'].replace(" ", "").upper(), '%I:%M%p'
        ).time() if 'AM' in x['startTime'].upper() or 'PM' in x['startTime'].upper() else x['startTime']
    )
    return today_classes


def get_teacher_stats(user, assigned_courses):
    assigned_course_ids = [c.id for c in assigned_courses]
    total_students = db.session.query(db.func.count(db.distinct(Enrollment.student_id)))\
        .filter(Enrollment.course_id.in_(assigned_course_ids)).scalar() or 0
    managed_courses_count = len(assigned_courses)
    avg_rating = db.session.query(db.func.avg(TeacherRating.rating))\
        .filter_by(teacher_id=user.id).scalar() or 0
    total_ratings = TeacherRating.query.filter_by(teacher_id=user.id).count()
    recent_reviews = TeacherRating.query.filter_by(teacher_id=user.id)\
        .order_by(TeacherRating.created_at.desc()).limit(5).all()

    return {
        'students': total_students,
        'courses': managed_courses_count,
        'rating': round(float(avg_rating), 1),
        'rating_count': total_ratings,
    }, recent_reviews


def get_teacher_graphs(assigned_courses):
    graphs_json = {}
    assigned_course_ids = [c.id for c in assigned_courses]

    grade_data = []
    for course in assigned_courses:
        avg_grade = db.session.query(db.func.avg(Grade.grade))\
            .filter_by(course_id=course.id).scalar() or 0
        grade_data.append({'Course': course.code, 'Avg Grade': round(avg_grade, 2)})

    if grade_data:
        df_grades = pd.DataFrame(grade_data)
        fig_grades = px.bar(df_grades, x='Course', y='Avg Grade',
                            title='Avg Grade per Class', template='plotly_dark')
        fig_grades.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        graphs_json['grades'] = json.dumps(fig_grades, cls=plotly.utils.PlotlyJSONEncoder)

    att_data = db.session.query(Attendance.status, db.func.count(Attendance.id))\
        .filter(Attendance.course_id.in_(assigned_course_ids))\
        .group_by(Attendance.status).all()
    if att_data:
        df_att = pd.DataFrame(att_data, columns=['Status', 'Count'])
        fig_att = px.pie(df_att, values='Count', names='Status',
                         title='Attendance Distribution', template='plotly_dark')
        fig_att.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        graphs_json['attendance'] = json.dumps(fig_att, cls=plotly.utils.PlotlyJSONEncoder)

    return graphs_json


def get_teacher_tasks(user_id):
    return TeacherTodo.query.filter_by(teacher_id=user_id)\
        .order_by(TeacherTodo.is_completed, TeacherTodo.created_at.desc()).all()


def get_user_courses(user, institution_id):
    if user.role in ('student', 'class_rep'):
        return (
            Course.query
            .join(Enrollment, Enrollment.course_id == Course.id)
            .join(Section, Course.section_id == Section.id)
            .filter(Enrollment.student_id == user.id, Section.institution_id == institution_id)
            .all()
        )
    elif user.role == 'professor':
        return (
            Course.query
            .join(Section)
            .filter(Course.teacher_id == user.id, Section.institution_id == institution_id)
            .all()
        )
    elif user.role == 'assistant_professor':
        return (
            Course.query
            .join(ProfessorAssistant, ProfessorAssistant.course_id == Course.id)
            .filter(
                ProfessorAssistant.assistant_teacher_id == user.id,
                ProfessorAssistant.is_active == True
            )
            .all()
        )
    elif user.role in ('dean', 'admin'):
        return (
            Course.query
            .join(Section)
            .filter(Section.institution_id == institution_id)
            .all()
        )
    return []


def update_meet_link(course_id, meet_link, user_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id == user_id:
        course.meet_link = meet_link
        db.session.commit()
        return True
    return False

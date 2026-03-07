from flask import Blueprint, render_template, g, flash, redirect, url_for, request
from ..middleware import school_scoped, owns_resource, role_minimum
from ..models import db, Course, Enrollment, Section, Announcement, Attendance, Grade, Assignment, Submission, Student, User, TeacherRating
from datetime import datetime

classroom_bp = Blueprint('classroom', __name__, url_prefix='/classroom')

@classroom_bp.route('/<int:course_id>/rate', methods=['POST'])
@school_scoped
def submit_rating(course_id):
    course = Course.query.get_or_404(course_id)
    rating_val = request.form.get('rating', type=int)
    review = request.form.get('review')
    anonymous = 'anonymous' in request.form

    if not rating_val or not (1 <= rating_val <= 5):
        flash('Invalid rating. Please select between 1-5.', 'danger')
        return redirect(url_for('classroom.view_classroom', course_id=course_id))

    existing = TeacherRating.query.filter_by(student_id=g.current_user.id, course_id=course_id).first()
    if existing:
        existing.rating = rating_val
        existing.review = review
        existing.is_anonymous = anonymous
    else:
        new_rating = TeacherRating(
            student_id=g.current_user.id,
            teacher_id=course.teacher_id,
            course_id=course_id,
            rating=rating_val,
            review=review,
            is_anonymous=anonymous
        )
        db.session.add(new_rating)
    
    db.session.commit()
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('classroom.view_classroom', course_id=course_id))

classroom_bp = Blueprint('classroom', __name__, url_prefix='/classroom')


@classroom_bp.route('/<int:course_id>')
@school_scoped
def view_classroom(course_id):
    user = g.current_user
    course = Course.query.get_or_404(course_id)
    owns_resource(course.section, 'school_id')

    if user.role in ('student', 'class_rep'):
        enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=course_id).first()
        if not enrollment:
            flash('Access Denied: You are not enrolled in this course.', 'danger')
            return redirect(url_for('dashboard.student_dashboard'))
        
        assignments = Assignment.query.filter_by(course_id=course_id).order_by(Assignment.due_date.asc()).all()
        announcements = Announcement.query.filter_by(course_id=course_id).order_by(Announcement.created_at.desc()).all()
        attendance_records = Attendance.query.filter_by(course_id=course_id, student_id=user.id).all()
        
        # Calculate grade average
        grades = Grade.query.filter_by(course_id=course_id, student_id=user.id).all()
        avg_grade = sum([g.grade for g in grades]) / len(grades) if grades else 0
        
        return render_template('classroom/student_view.html', 
                               course=course, 
                               assignments=assignments, 
                               announcements=announcements,
                               attendance=attendance_records,
                               avg_grade=round(avg_grade, 2))

    elif user.role in ('teacher', 'assistant', 'dean', 'timetable_manager'):
        if user.role in ('teacher', 'assistant') and course.teacher_id != user.id:
            flash('Access Denied: This is not your course.', 'danger')
            return redirect(url_for('dashboard.teacher_dashboard'))
        
        # Professor views: Student list with stats
        enrolled_students = Enrollment.query.filter_by(course_id=course_id).all()
        students_data = []
        for e in enrolled_students:
            student = e.student_user
            att_count = Attendance.query.filter_by(course_id=course_id, student_id=student.id, status='present').count()
            total_classes = Attendance.query.filter_by(course_id=course_id, student_id=student.id).count() or 1
            att_pct = (att_count / total_classes) * 100
            
            grade_avg = db.session.query(db.func.avg(Grade.grade)).filter_by(course_id=course_id, student_id=student.id).scalar() or 0
            
            students_data.append({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'attendance': round(att_pct, 1),
                'grade': round(float(grade_avg), 1),
                'risk': 'high' if att_pct < 75 or grade_avg < 40 else 'low'
            })
            
        assignments = Assignment.query.filter_by(course_id=course_id).all()
        announcements = Announcement.query.filter_by(course_id=course_id).all()
        
        return render_template('classroom/teacher_view.html', 
                               course=course, 
                               students=students_data,
                               assignments=assignments,
                               announcements=announcements)

    return redirect(url_for('index'))


@classroom_bp.route('/<int:course_id>/attendance/mark', methods=['POST'])
@school_scoped
@role_minimum('teacher')
def mark_attendance(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != g.current_user.id:
        return {"error": "Unauthorized"}, 403
        
    date_str = request.form.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    status_data = request.form.getlist('status') # format: student_id:status
    
    for item in status_data:
        sid, status = item.split(':')
        # Check if exists for this date
        att = Attendance.query.filter_by(course_id=course_id, student_id=sid, date=datetime.strptime(date_str, '%Y-%m-%d').date()).first()
        if att:
            att.status = status
        else:
            db.session.add(Attendance(course_id=course_id, student_id=sid, status=status, date=datetime.strptime(date_str, '%Y-%m-%d').date()))
            
    db.session.commit()
    flash('Attendance marked successfully.', 'success')
    return redirect(url_for('classroom.view_classroom', course_id=course_id))


@classroom_bp.route('/<int:course_id>/assignments/create', methods=['POST'])
@school_scoped
@role_minimum('teacher')
def create_assignment(course_id):
    title = request.form.get('title')
    desc = request.form.get('description')
    due_date = request.form.get('due_date')
    points = request.form.get('points', 100)
    
    new_assignment = Assignment(
        course_id=course_id,
        title=title,
        description=desc,
        due_date=datetime.strptime(due_date, '%Y-%m-%dT%H:%M'),
        max_points=points
    )
    db.session.add(new_assignment)
    db.session.commit()
    flash('Assignment created.', 'success')
    return redirect(url_for('classroom.view_classroom', course_id=course_id))


@classroom_bp.route('/<int:course_id>/announcements/post', methods=['POST'])
@school_scoped
def post_announcement(course_id):
    title = request.form.get('title')
    body = request.form.get('body')
    urgent = 'urgent' in request.form
    
    ann = Announcement(
        school_id=g.current_user.school_id,
        course_id=course_id,
        teacher_id=g.current_user.id,
        title=title,
        body=body,
        urgent=urgent
    )
    db.session.add(ann)
    db.session.commit()
    flash('Announcement posted.', 'success')
    return redirect(url_for('classroom.view_classroom', course_id=course_id))

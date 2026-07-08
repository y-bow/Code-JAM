from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort
from datetime import datetime
from ..middleware import school_scoped, role_minimum
from ..models import (
    db, User, Student, Section, Course, School,
    Announcement, TimetableEntry
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@school_scoped
@role_minimum('admin')
def admin_dashboard():
    total_schools = School.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_professors = User.query.filter_by(role='professor').count()
    total_courses = Course.query.count()

    schools = School.query.all()
    school_data = []
    for s in schools:
        s_students = User.query.filter_by(school_id=s.id, role='student').count()
        s_professors = User.query.filter_by(school_id=s.id, role='professor').count()
        s_courses = Course.query.join(Section).filter(Section.school_id == s.id).count()

        avg_cgpa = db.session.query(db.func.avg(Student.cgpa)).join(User).filter(User.school_id == s.id).scalar() or 0

        school_data.append({
            'name': s.name,
            'students': s_students,
            'professors': s_professors,
            'courses': s_courses,
            'avg_cgpa': round(float(avg_cgpa), 2),
            'avg_attendance': "85%",
            'status': 'active' if s.is_active else 'inactive'
        })

    return render_template('dashboard/admin_dashboard_global.html',
                           stats={
                               'schools': total_schools,
                               'students': total_students,
                               'professors': total_professors,
                               'courses': total_courses,
                               'sections': Section.query.count()
                           },
                           school_data=school_data,
                           schools=schools,
                           announcements=Announcement.query.filter_by(school_id=None).order_by(Announcement.posted_at.desc()).limit(5).all())


@admin_bp.route('/schools')
@school_scoped
@role_minimum('admin')
def admin_schools():
    if g.current_user.role != 'admin':
        abort(403)
    schools = School.query.all()
    return render_template('dashboard/admin_schools.html', schools=schools)


@admin_bp.route('/schools/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def add_school():
    if g.current_user.role != 'admin':
        abort(403)
    name = request.form.get('name')
    code = request.form.get('code')
    domain = request.form.get('domain')

    if not name or not code:
        flash('Name and Code are required.', 'danger')
        return redirect(url_for('admin.admin_schools'))

    new_school = School(name=name, code=code, domain=domain)
    db.session.add(new_school)
    db.session.commit()
    flash('School added successfully!', 'success')
    return redirect(url_for('admin.admin_schools'))


@admin_bp.route('/schools/toggle/<string:school_id>', methods=['POST'])
@school_scoped
@role_minimum('admin')
def toggle_school(school_id):
    if g.current_user.role != 'admin':
        abort(403)
    school = School.query.get_or_404(school_id)
    school.is_active = not school.is_active
    db.session.commit()
    status = 'activated' if school.is_active else 'suspended'
    flash(f'School {school.name} has been {status}.', 'info')
    return redirect(url_for('admin.admin_schools'))


@admin_bp.route('/sections')
@school_scoped
@role_minimum('admin')
def admin_sections():
    if g.current_user.role == 'admin':
        sections = Section.query.all()
        schools = School.query.all()
    else:
        sections = Section.query.filter_by(school_id=g.school_id).all()
        schools = [g.current_user.school]
    return render_template('dashboard/admin_sections.html', sections=sections, schools=schools)


@admin_bp.route('/sections/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def add_section():
    school_id = request.form.get('school_id', type=int)
    name = request.form.get('name')
    code = request.form.get('code')
    batch_year = request.form.get('batch_year', type=int)

    if g.current_user.role != 'admin' and school_id != g.school_id:
        abort(403)

    new_section = Section(school_id=school_id, name=name, code=code, batch_year=batch_year)
    db.session.add(new_section)
    db.session.commit()
    flash('Section added successfully!', 'success')
    return redirect(url_for('admin.admin_sections'))


@admin_bp.route('/accounts')
@school_scoped
@role_minimum('admin')
def admin_accounts():
    if g.current_user.role == 'admin':
        users = User.query.all()
        schools = School.query.all()
    else:
        users = User.query.filter_by(school_id=g.school_id).all()
        schools = [g.current_user.school]
    return render_template('dashboard/admin_accounts.html', users=users, schools=schools)


@admin_bp.route('/accounts/toggle/<string:user_id>', methods=['POST'])
@school_scoped
@role_minimum('admin')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if g.current_user.role != 'admin' and user.school_id != g.school_id:
        abort(403)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.name} has been {status}.', 'info')
    return redirect(url_for('admin.admin_accounts'))


@admin_bp.route('/settings')
@school_scoped
@role_minimum('admin')
def admin_settings():
    return render_template('dashboard/admin_settings.html')


@admin_bp.route('/announcements')
@school_scoped
def announcements():
    user = g.current_user
    my_section_id = None
    if user.role == 'student':
        profile = user.student_profile
        if profile:
            my_section_id = profile.section_id

    query = Announcement.query.filter(Announcement.school_id == g.school_id)
    if my_section_id:
        query = query.filter(
            (Announcement.section_id == None) |
            (Announcement.section_id == my_section_id)
        )

    announcements_list = query.order_by(Announcement.posted_at.desc()).all()
    return render_template('dashboard/announcements.html', announcements=announcements_list)

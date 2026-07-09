from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort
from ..middleware import school_scoped, role_minimum
from ..models import (
    db, User, Student, Section, Course, Institution,
    AcademicUnit, Department, Program, AcademicYear,
    Announcement, TimetableEntry
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin',
                      template_folder='templates/admin')


@admin_bp.route('/dashboard')
@school_scoped
@role_minimum('admin')
def admin_dashboard():
    user = g.current_user
    if user.role == 'admin':
        institution = Institution.query.get(g.institution_id)
        institutions = [institution] if institution else []
    else:
        institutions = Institution.query.all()

    institution_data = []
    for inst in institutions:
        s_students = User.query.filter_by(institution_id=inst.id, role='student').count()
        s_professors = User.query.filter_by(institution_id=inst.id, role='professor').count()
        s_courses = Course.query.join(Section).filter(Section.institution_id == inst.id).count()
        avg_cgpa = db.session.query(db.func.avg(Student.cgpa)).join(User).filter(User.institution_id == inst.id).scalar() or 0

        institution_data.append({
            'name': inst.name,
            'students': s_students,
            'professors': s_professors,
            'courses': s_courses,
            'avg_cgpa': round(float(avg_cgpa), 2),
            'avg_attendance': '85%',
            'status': 'active' if inst.is_active else 'inactive'
        })

    is_first_login = False
    if g.current_user.created_at:
        is_first_login = datetime.utcnow() - g.current_user.created_at < timedelta(minutes=30)

    return render_template('admin_dashboard_global.html',
                           stats={
                               'schools': Institution.query.count(),
                               'students': User.query.filter_by(role='student').count(),
                               'professors': User.query.filter_by(role='professor').count(),
                               'courses': Course.query.count(),
                               'sections': Section.query.count()
                           },
                           school_data=institution_data,
                           schools=institutions,
                           announcements=Announcement.query.filter_by(institution_id=None).order_by(Announcement.posted_at.desc()).limit(5).all(),
                           is_first_login=is_first_login)


@admin_bp.route('/institutions')
@school_scoped
@role_minimum('admin')
def admin_institutions():
    if g.current_user.role != 'admin':
        abort(403)
    institutions = Institution.query.all()
    return render_template('admin_schools.html', schools=institutions)


@admin_bp.route('/institutions/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def add_institution():
    if g.current_user.role != 'admin':
        abort(403)
    name = request.form.get('name')
    code = request.form.get('code')
    domain = request.form.get('domain')

    if not name or not code:
        flash('Name and Code are required.', 'danger')
        return redirect(url_for('admin.admin_institutions'))

    new_inst = Institution(name=name, code=code, domain=domain)
    db.session.add(new_inst)
    db.session.commit()
    flash('Institution added successfully!', 'success')
    return redirect(url_for('admin.admin_institutions'))


@admin_bp.route('/institutions/toggle/<string:institution_id>', methods=['POST'])
@school_scoped
@role_minimum('admin')
def toggle_institution(institution_id):
    if g.current_user.role != 'admin':
        abort(403)
    institution = Institution.query.get_or_404(institution_id)
    institution.is_active = not institution.is_active
    db.session.commit()
    status = 'activated' if institution.is_active else 'suspended'
    flash(f'Institution {institution.name} has been {status}.', 'info')
    return redirect(url_for('admin.admin_institutions'))


@admin_bp.route('/academic-units')
@school_scoped
@role_minimum('admin')
def admin_academic_units():
    if g.current_user.role == 'admin':
        units = AcademicUnit.query.all()
        institutions = Institution.query.all()
    else:
        units = AcademicUnit.query.filter_by(institution_id=g.institution_id).all()
        institutions = [Institution.query.get(g.institution_id)]
    return render_template('admin_academic_units.html', academic_units=units, institutions=institutions)


@admin_bp.route('/academic-units/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def add_academic_unit():
    institution_id = request.form.get('institution_id', g.institution_id, type=str)
    name = request.form.get('name')
    code = request.form.get('code')

    if not name or not code:
        flash('Name and Code are required.', 'danger')
        return redirect(url_for('admin.admin_academic_units'))

    unit = AcademicUnit(institution_id=institution_id, name=name, code=code)
    db.session.add(unit)
    db.session.commit()
    flash('Academic unit added successfully!', 'success')
    return redirect(url_for('admin.admin_academic_units'))


@admin_bp.route('/departments')
@school_scoped
@role_minimum('admin')
def admin_departments():
    if g.current_user.role == 'admin':
        departments = Department.query.all()
        institutions = Institution.query.all()
    else:
        departments = Department.query.filter_by(institution_id=g.institution_id).all()
        institutions = [Institution.query.get(g.institution_id)]
    return render_template('admin_departments.html', departments=departments, institutions=institutions)


@admin_bp.route('/departments/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def add_department():
    institution_id = request.form.get('institution_id', g.institution_id, type=str)
    name = request.form.get('name')
    code = request.form.get('code')

    if not name or not code:
        flash('Name and Code are required.', 'danger')
        return redirect(url_for('admin.admin_departments'))

    dept = Department(institution_id=institution_id, name=name, code=code)
    db.session.add(dept)
    db.session.commit()
    flash('Department added successfully!', 'success')
    return redirect(url_for('admin.admin_departments'))


@admin_bp.route('/programs')
@school_scoped
@role_minimum('admin')
def admin_programs():
    if g.current_user.role == 'admin':
        programs = Program.query.all()
        departments = Department.query.all()
    else:
        dept_ids = [d.id for d in Department.query.filter_by(institution_id=g.institution_id).all()]
        programs = Program.query.filter(Program.department_id.in_(dept_ids)).all()
        departments = Department.query.filter_by(institution_id=g.institution_id).all()
    return render_template('admin_programs.html', programs=programs, departments=departments)


@admin_bp.route('/programs/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def add_program():
    department_id = request.form.get('department_id', type=str)
    name = request.form.get('name')
    code = request.form.get('code')
    duration_years = request.form.get('duration_years', 4, type=int)

    if not name or not code or not department_id:
        flash('Name, Code, and Department are required.', 'danger')
        return redirect(url_for('admin.admin_programs'))

    prog = Program(department_id=department_id, name=name, code=code, duration_years=duration_years)
    db.session.add(prog)
    db.session.commit()
    flash('Program added successfully!', 'success')
    return redirect(url_for('admin.admin_programs'))


@admin_bp.route('/sections')
@school_scoped
@role_minimum('admin')
def admin_sections():
    if g.current_user.role == 'admin':
        sections = Section.query.all()
        institutions = Institution.query.all()
    else:
        sections = Section.query.filter_by(institution_id=g.institution_id).all()
        institutions = [Institution.query.get(g.institution_id)]
    return render_template('admin_sections.html', sections=sections, schools=institutions)


@admin_bp.route('/sections/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def add_section():
    institution_id = request.form.get('institution_id', g.institution_id, type=str)
    program_id = request.form.get('program_id', type=str)
    name = request.form.get('name')
    code = request.form.get('code')
    batch_year = request.form.get('batch_year', type=int)
    department_id = request.form.get('department_id', type=str)

    if g.current_user.role != 'admin' and institution_id != g.institution_id:
        abort(403)

    new_section = Section(
        institution_id=institution_id,
        program_id=program_id or code,
        department_id=department_id,
        name=name, code=code, batch_year=batch_year
    )
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
        institutions = Institution.query.all()
    else:
        users = User.query.filter_by(institution_id=g.institution_id).all()
        institutions = [Institution.query.get(g.institution_id)]
    return render_template('admin_accounts.html', users=users, schools=institutions)


@admin_bp.route('/accounts/toggle/<string:user_id>', methods=['POST'])
@school_scoped
@role_minimum('admin')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if g.current_user.role != 'admin' and user.institution_id != g.institution_id:
        abort(403)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.name} has been {status}.', 'info')
    return redirect(url_for('admin.admin_accounts'))


@admin_bp.route('/settings', methods=['GET', 'POST'])
@school_scoped
@role_minimum('admin')
def admin_settings():
    from ..models import set_setting

    if request.method == 'POST':
        import re

        theme_mode = request.form.get('theme_mode', 'light')
        primary_color = request.form.get('primary_color', '#2563eb')
        if not re.match(r'^#[0-9A-Fa-f]{6}$', primary_color):
            flash('Invalid color format. Use a hex color like #2563eb.', 'danger')
            return redirect(url_for('admin.admin_settings'))
        set_setting('theme.active', theme_mode)
        set_setting('theme.primary_color', primary_color)

        institution_name = request.form.get('school_name', '').strip()
        if institution_name:
            set_setting('school.name', institution_name)
        set_setting('school.department', request.form.get('school_department', '').strip())
        set_setting('school.address', request.form.get('school_address', '').strip())
        set_setting('school.finance_email', request.form.get('school_finance_email', '').strip())

        currency = request.form.get('fees_currency_symbol', '').strip()
        if currency:
            set_setting('fees.currency_symbol', currency)

        cgpa_str = request.form.get('early_warning_cgpa_threshold', '').strip()
        if cgpa_str:
            try:
                set_setting('early_warning.cgpa_threshold', float(cgpa_str), 'float')
            except ValueError:
                flash('Invalid CGPA threshold. Must be a number.', 'danger')
                return redirect(url_for('admin.admin_settings'))
        att_str = request.form.get('early_warning_attendance_threshold', '').strip()
        if att_str:
            try:
                set_setting('early_warning.attendance_threshold', int(att_str), 'int')
            except ValueError:
                flash('Invalid attendance threshold. Must be a whole number.', 'danger')
                return redirect(url_for('admin.admin_settings'))

        default_pw = request.form.get('import_default_password', '').strip()
        if default_pw:
            set_setting('import.default_password', default_pw)

        flash('All settings saved!', 'success')
        return redirect(url_for('admin.admin_settings'))

    return render_template('admin_settings.html')


@admin_bp.route('/announcements')
@school_scoped
def announcements():
    user = g.current_user
    my_section_id = None
    if user.role == 'student':
        profile = user.student_profile
        if profile:
            my_section_id = profile.section_id

    query = Announcement.query.filter(Announcement.institution_id == g.institution_id)
    if my_section_id:
        query = query.filter(
            (Announcement.section_id == None) |
            (Announcement.section_id == my_section_id)
        )

    announcements_list = query.order_by(Announcement.posted_at.desc()).all()
    return render_template('announcements.html', announcements=announcements_list)

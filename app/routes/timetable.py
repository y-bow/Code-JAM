from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort, jsonify
from ..middleware import school_scoped, role_minimum
from ..models import db, Section, TimetableEntry, School
from ..services import (
    format_time_12hr,
    get_student_timetable_data,
    get_teacher_timetable_data,
    get_system_timetable_data,
    get_common_free_slots,
    update_timetable_entry,
    create_timetable_entry,
    cancel_timetable_entry,
    restore_timetable_entry,
    delete_timetable_entry,
    manage_add_entry,
    manage_delete_entry,
)

timetable_bp = Blueprint('timetable', __name__, url_prefix='/timetable',
                          template_folder='templates/timetable')


@timetable_bp.route('/admin')
@school_scoped
@role_minimum('admin')
def admin_timetable():
    if g.current_user.role == 'admin':
        sections = Section.query.all()
    else:
        sections = Section.query.filter_by(school_id=g.school_id).all()
    selected_section_id = request.args.get('section_id', type=int)

    if not selected_section_id and sections:
        selected_section_id = sections[0].id

    timetable = [[] for _ in range(5)]
    selected_section = None

    if selected_section_id:
        selected_section = Section.query.get(selected_section_id)
        if selected_section and (g.current_user.role == 'admin' or selected_section.school_id == g.school_id):
            for day_idx in range(5):
                entries = TimetableEntry.query.filter_by(
                    section_id=selected_section_id,
                    day=day_idx
                ).order_by(TimetableEntry.start_time).all()
                timetable[day_idx] = [e.to_dict() for e in entries]
                for i, d in enumerate(timetable[day_idx]):
                    d['id'] = entries[i].id

    return render_template('admin_timetable.html',
                           sections=sections,
                           selected_section=selected_section,
                           timetable=timetable)


@timetable_bp.route('/admin/debug')
@school_scoped
@role_minimum('admin')
def timetable_debug():
    query = TimetableEntry.query.join(Section)
    if g.current_user.role != 'admin':
        query = query.filter(Section.school_id == g.school_id)
    rows = query.all()
    return jsonify([r.to_dict() for r in rows])


@timetable_bp.route('/admin/update', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_update():
    entry_id = request.form.get('entry_id', type=int)
    section_id, error = update_timetable_entry(
        entry_id=entry_id,
        new_subject=request.form.get('subject'),
        new_teacher=request.form.get('teacher'),
        new_period=request.form.get('period'),
        new_room=request.form.get('room'),
        new_start=format_time_12hr(request.form.get('start_time')),
        new_end=format_time_12hr(request.form.get('end_time')),
        school_id=g.school_id if g.current_user.role != 'admin' else None,
        user_id=g.current_user.id,
    )
    if error:
        abort(403)
    flash("Timetable updated. Announcement sent.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=section_id))


@timetable_bp.route('/admin/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_add():
    section_id, error = create_timetable_entry(
        section_id=request.form.get('section_id', type=int),
        day=request.form.get('day', type=int),
        start_time=format_time_12hr(request.form.get('start_time')),
        end_time=format_time_12hr(request.form.get('end_time')),
        subject=request.form.get('subject'),
        teacher=request.form.get('teacher'),
        room=request.form.get('room'),
        period=request.form.get('period'),
        color=request.form.get('color', 'var(--primary-color)'),
        school_id=g.school_id,
        user_id=g.current_user.id,
    )
    if error:
        abort(403)
    flash("Timetable updated. Announcement sent.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=section_id))


@timetable_bp.route('/admin/cancel', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_cancel():
    section_id, error = cancel_timetable_entry(
        entry_id=request.form.get('entry_id', type=int),
        school_id=g.school_id,
        user_id=g.current_user.id,
    )
    if error:
        abort(403)
    flash("Class cancelled. Announcement sent.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=section_id))


@timetable_bp.route('/admin/restore', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_restore():
    section_id, error = restore_timetable_entry(
        entry_id=request.form.get('entry_id', type=int),
        school_id=g.school_id,
        user_id=g.current_user.id,
    )
    if error:
        abort(403)
    flash("Class restored. Announcement sent.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=section_id))


@timetable_bp.route('/admin/delete', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_delete():
    section_id, error = delete_timetable_entry(
        entry_id=request.form.get('entry_id', type=int),
        school_id=g.school_id,
        user_id=g.current_user.id,
    )
    if error:
        abort(403)
    flash("Class permanently deleted. Announcement sent.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=section_id))


@timetable_bp.route('/', methods=['GET', 'POST'])
@school_scoped
def timetable():
    user = g.current_user

    my_section_id = None
    if user.role == 'student':
        profile = user.student_profile
        if profile and profile.section_id:
            my_section_id = profile.section_id

    timetable_data = {}
    if my_section_id:
        student_lab_section = user.student_profile.lab_section if user.student_profile else None
        timetable_data = get_student_timetable_data(my_section_id, student_lab_section)

    current_day = __import__('datetime').datetime.now().weekday()
    if current_day > 4:
        current_day = -1

    if user.role in ['professor', 'assistant_professor']:
        result = get_teacher_timetable_data(user.id)
        return render_template('timetable_teacher.html',
                               timetable_data=result['timetable_data'],
                               current_day=current_day,
                               total_classes=result['total_classes'],
                               teaching_hours=result['teaching_hours'],
                               sections_taught=result['sections_taught'])

    elif user.role in ['student', 'class_rep']:
        sections = []
        my_section = None
        selected_section = None
        free_slots_by_day = None

        if my_section_id:
            my_section = Section.query.get(my_section_id)
            sections = Section.query.join(School).order_by(School.name, Section.name).all()

            if request.method == 'POST':
                selected_section_id = request.form.get('compare_section_id', type=int)
                if selected_section_id:
                    selected_section = Section.query.get(selected_section_id)
                    if selected_section:
                        free_slots_by_day = get_common_free_slots(my_section_id, selected_section_id)

        return render_template('timetable.html',
                             timetable_data=timetable_data,
                             current_day=current_day,
                             sections=sections,
                             my_section=my_section,
                             selected_section=selected_section,
                             free_slots_by_day=free_slots_by_day)

    else:
        all_entries = get_system_timetable_data()
        return render_template('timetable_system.html', all_entries=all_entries)


@timetable_bp.route('/manage', methods=['GET', 'POST'])
@school_scoped
@role_minimum('admin')
def manage_timetable():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            success, msg = manage_add_entry(
                section_id=request.form.get('section_id'),
                day=int(request.form.get('day')),
                start_time=request.form.get('start_time'),
                end_time=request.form.get('end_time'),
                title=request.form.get('title'),
                room=request.form.get('room'),
                color=request.form.get('color', 'var(--primary-color)'),
                school_id=g.school_id,
            )
            flash(msg, 'success' if success else 'danger')
        elif action == 'delete':
            success, msg = manage_delete_entry(
                entry_id=request.form.get('entry_id'),
                school_id=g.school_id,
            )
            flash(msg, 'info' if success else 'danger')

        return redirect(url_for('timetable.manage_timetable'))

    sections = Section.query.filter_by(school_id=g.school_id).all()
    entries = (
        TimetableEntry.query
        .join(Section)
        .filter(Section.school_id == g.school_id)
        .order_by(Section.code, TimetableEntry.day, TimetableEntry.start_time)
        .all()
    )
    return render_template('manage_timetable.html', sections=sections, entries=entries)

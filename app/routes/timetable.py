from flask import Blueprint, render_template, session, request, redirect, url_for, g, flash, abort, jsonify
from datetime import datetime
from ..middleware import school_scoped, role_minimum
from ..models import (
    db, User, Student, Course, Section, Announcement,
    TimetableEntry, School
)

timetable_bp = Blueprint('timetable', __name__, url_prefix='/timetable')


def format_time_12hr(time_str):
    if not time_str: return ""
    time_str = time_str.strip()
    try:
        if ':' in time_str and 'AM' not in time_str.upper() and 'PM' not in time_str.upper():
            from datetime import datetime
            t = datetime.strptime(time_str[:5], "%H:%M")
            return t.strftime("%I:%M%p").lstrip('0')
    except:
        pass
    return time_str.replace(" ", "")


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

    return render_template('dashboard/admin_timetable.html',
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
    new_subject = request.form.get('subject')
    new_teacher = request.form.get('teacher')
    new_period = request.form.get('period')
    new_room = request.form.get('room')
    new_start = format_time_12hr(request.form.get('start_time'))
    new_end = format_time_12hr(request.form.get('end_time'))

    entry = TimetableEntry.query.get_or_404(entry_id)
    if g.current_user.role != 'admin' and entry.section.school_id != g.school_id:
        abort(403)

    old_subject = entry.title
    old_room = entry.room
    old_teacher = entry.teacher
    old_start = entry.start_time
    old_end = entry.end_time

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_name = days[entry.day] if 0 <= entry.day < 5 else "Unspecified Day"

    if new_start: entry.start_time = new_start
    if new_end: entry.end_time = new_end

    if new_subject and new_subject != old_subject:
        entry.title = new_subject
        body = f"Timetable Update ({entry.section.name}): {day_name} {entry.start_time}-{entry.end_time} — '{old_subject}' has been changed to '{new_subject}'."
        db.session.add(Announcement(school_id=g.school_id, section_id=entry.section_id, teacher_id=g.current_user.id, category='timetable', title="Timetable Update", body=body))

    if new_room and new_room != old_room:
        entry.room = new_room
        body = f"Room Change ({entry.section.name}): {entry.title} on {day_name} {entry.start_time}-{entry.end_time} has moved from {old_room} to {new_room}."
        db.session.add(Announcement(school_id=g.school_id, section_id=entry.section_id, teacher_id=g.current_user.id, category='timetable', title="Room Change", body=body))

    if new_teacher and new_teacher != old_teacher:
        entry.teacher = new_teacher
        body = f"Teacher Change ({entry.section.name}): {entry.title} on {day_name} will now be taught by {new_teacher} instead of {old_teacher}."
        db.session.add(Announcement(school_id=g.school_id, section_id=entry.section_id, teacher_id=g.current_user.id, category='timetable', title="Teacher Change", body=body))

    entry.period = new_period
    db.session.commit()

    flash(f"Timetable updated. Announcement sent to Section {entry.section.name} students.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=entry.section_id))


@timetable_bp.route('/admin/add', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_add():
    section_id = request.form.get('section_id', type=int)
    day = request.form.get('day', type=int)
    start_time = format_time_12hr(request.form.get('start_time'))
    end_time = format_time_12hr(request.form.get('end_time'))
    subject = request.form.get('subject')
    teacher = request.form.get('teacher')
    room = request.form.get('room')
    period = request.form.get('period')
    color = request.form.get('color', 'var(--primary-color)')

    section = Section.query.get_or_404(section_id)
    if section.school_id != g.school_id:
        abort(403)

    new_entry = TimetableEntry(
        section_id=section_id,
        day=day,
        start_time=start_time,
        end_time=end_time,
        title=subject,
        teacher=teacher,
        room=room,
        period=period,
        color=color,
        status='active'
    )
    db.session.add(new_entry)
    db.session.commit()

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_name = days[day] if 0 <= day < 5 else "Unspecified Day"

    announcement = Announcement(
        school_id=g.school_id,
        section_id=section_id,
        teacher_id=g.current_user.id,
        category='timetable',
        title="New Class Added",
        body=f"New Class ({section.name}): {subject} added on {day_name} from {start_time} to {end_time} in {room} with {teacher}.",
        posted_at=datetime.utcnow()
    )
    db.session.add(announcement)
    db.session.commit()

    flash(f"Timetable updated. Announcement sent to Section {section.name} students.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=section_id))


@timetable_bp.route('/admin/cancel', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_cancel():
    entry_id = request.form.get('entry_id', type=int)
    entry = TimetableEntry.query.get_or_404(entry_id)

    if entry.section.school_id != g.school_id:
        abort(403)

    entry.status = 'cancelled'
    db.session.commit()

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_name = days[entry.day] if 0 <= entry.day < 5 else "Unspecified Day"

    announcement = Announcement(
        school_id=g.school_id,
        section_id=entry.section_id,
        teacher_id=g.current_user.id,
        category='timetable',
        title="Class Cancelled",
        body=f"Class Cancelled (Section {entry.section.name}): {entry.title} on {day_name} ({entry.start_time}-{entry.end_time}) has been cancelled.",
        posted_at=datetime.utcnow()
    )
    db.session.add(announcement)
    db.session.commit()

    flash(f"Class cancelled. Announcement sent to Section {entry.section.name} students.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=entry.section_id))


@timetable_bp.route('/admin/restore', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_restore():
    entry_id = request.form.get('entry_id', type=int)
    entry = TimetableEntry.query.get_or_404(entry_id)

    if entry.section.school_id != g.school_id:
        abort(403)

    entry.status = 'active'
    db.session.commit()

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_name = days[entry.day] if 0 <= entry.day < 5 else "Unspecified Day"

    announcement = Announcement(
        school_id=g.school_id,
        section_id=entry.section_id,
        teacher_id=g.current_user.id,
        category='timetable',
        title="Class Restored",
        body=f"Class Restored (Section {entry.section.name}): {entry.title} on {day_name} ({entry.start_time}-{entry.end_time}) is back on schedule.",
        posted_at=datetime.utcnow()
    )
    db.session.add(announcement)
    db.session.commit()

    flash(f"Class restored. Announcement sent to Section {entry.section.name} students.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=entry.section_id))


@timetable_bp.route('/admin/delete', methods=['POST'])
@school_scoped
@role_minimum('admin')
def admin_timetable_delete():
    entry_id = request.form.get('entry_id', type=int)
    entry = TimetableEntry.query.get_or_404(entry_id)

    if entry.section.school_id != g.school_id:
        abort(403)

    section_id = entry.section_id
    section_name = entry.section.name
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_name = days[entry.day] if 0 <= entry.day < 5 else "Unspecified Day"
    info = f"{entry.title} on {day_name} ({entry.start_time}-{entry.end_time})"

    db.session.delete(entry)
    db.session.commit()

    announcement = Announcement(
        school_id=g.school_id,
        section_id=section_id,
        teacher_id=g.current_user.id,
        category='timetable',
        title="Class Removed",
        body=f"Class Removed (Section {section_name}): {info} has been permanently removed from the timetable.",
        posted_at=datetime.utcnow()
    )
    db.session.add(announcement)
    db.session.commit()

    flash(f"Class permanently deleted. Announcement sent to Section {section_name} students.", "success")
    return redirect(url_for('timetable.admin_timetable', section_id=section_id))


@timetable_bp.route('/', methods=['GET', 'POST'])
@school_scoped
def timetable():
    user = g.current_user

    timetable_data = {}
    my_section_id = None
    if user.role == 'student':
        profile = user.student_profile
        if profile and profile.section_id:
            my_section_id = profile.section_id

    if my_section_id:
        student_lab_section = user.student_profile.lab_section if user.student_profile else None
        for day_idx in range(6):
            entries = TimetableEntry.query.filter_by(
                section_id=my_section_id,
                day=day_idx
            ).order_by(TimetableEntry.start_time).all()

            if student_lab_section is not None and student_lab_section != 3:
                entries = [e for e in entries if '(LAB)' not in e.title]

            timetable_data[day_idx] = [
                {
                    'startTime': e.start_time,
                    'endTime': e.end_time,
                    'title': e.title,
                    'room': e.room,
                    'color': e.color or 'var(--primary-color)',
                    'status': e.status
                } for e in entries
            ]

        for day in timetable_data:
            timetable_data[day].sort(key=lambda x: datetime.strptime(x['startTime'].replace(" ", "").upper(), '%I:%M%p').time() if 'AM' in x['startTime'].upper() or 'PM' in x['startTime'].upper() else x['startTime'])

    current_day = datetime.now().weekday()
    if current_day > 4:
        current_day = -1

    if user.role in ['professor', 'assistant_professor']:
        entries = db.session.query(TimetableEntry, Course, Section)\
            .join(Course, TimetableEntry.course_id == Course.id)\
            .join(Section, TimetableEntry.section_id == Section.id)\
            .filter(Course.teacher_id == user.id)\
            .order_by(TimetableEntry.day, TimetableEntry.start_time)\
            .all()

        timetable_data = {i: [] for i in range(5)}
        sections_taught = set()
        teaching_minutes = 0
        total_classes = len(entries)

        for e, c, s in entries:
            try:
                st = datetime.strptime(e.start_time.replace(" ", "").upper(), '%I:%M%p')
                et = datetime.strptime(e.end_time.replace(" ", "").upper(), '%I:%M%p')
                duration = int((et - st).total_seconds() / 60)
                teaching_minutes += duration
            except Exception:
                duration = 0

            if 0 <= e.day <= 4:
                timetable_data[e.day].append({
                    'course_name': c.name,
                    'course_code': c.code,
                    'section': s.code,
                    'start_time': e.start_time,
                    'end_time': e.end_time,
                    'room': e.room,
                    'status': e.status,
                    'color': e.color or 'var(--primary-color)',
                    'duration': duration
                })
            sections_taught.add(s.code)

        for day in timetable_data:
            timetable_data[day].sort(key=lambda x: datetime.strptime(x['start_time'].replace(" ", "").upper(), '%I:%M%p').time() if 'AM' in x['start_time'].upper() or 'PM' in x['start_time'].upper() else x['start_time'])

        hours = teaching_minutes // 60
        mins = teaching_minutes % 60
        teaching_hours_str = f"{hours}h {mins}m"

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        return render_template('dashboard/timetable_teacher.html',
                               timetable_data=timetable_data,
                               current_day=current_day,
                               total_classes=total_classes,
                               teaching_hours=teaching_hours_str,
                               sections_taught=sorted(list(sections_taught)))

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

        return render_template('dashboard/timetable.html',
                             timetable_data=timetable_data,
                             current_day=current_day,
                             sections=sections,
                             my_section=my_section,
                             selected_section=selected_section,
                             free_slots_by_day=free_slots_by_day)

    else:
        all_entries = db.session.query(TimetableEntry, Section)\
            .join(Section, TimetableEntry.section_id == Section.id)\
            .order_by(TimetableEntry.day, TimetableEntry.start_time).all()
        return render_template('dashboard/timetable_system.html', all_entries=all_entries)


def get_common_free_slots(section_a_id, section_b_id):
    entries_a = TimetableEntry.query.filter_by(section_id=section_a_id).all()
    entries_b = TimetableEntry.query.filter_by(section_id=section_b_id).all()

    section_b_courses = Course.query.filter_by(section_id=section_b_id).all()
    course_teacher_map = {}
    for c in section_b_courses:
        if c.teacher:
            course_teacher_map[c.name] = c.teacher.name

    def to_minutes(t_str):
        t = datetime.strptime(t_str.strip().replace(" ", "").upper(), "%I:%M%p")
        return t.hour * 60 + t.minute

    def to_time_str(mins):
        h = mins // 60
        m = mins % 60
        is_pm = h >= 12
        display_h = h if h <= 12 else h - 12
        if display_h == 0: display_h = 12
        ampm = "PM" if is_pm else "AM"
        return f"{display_h}:{m:02d} {ampm}"

    DAYS_MAP = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday'}
    DAY_START = 9 * 60
    DAY_END = 17 * 60 + 15

    free_slots_by_day = []

    for day_idx in range(5):
        busy_intervals = []
        b_day_entries = []
        for e in entries_a + entries_b:
            if e.day == day_idx:
                try:
                    start_m = to_minutes(e.start_time)
                    end_m = to_minutes(e.end_time)
                    busy_intervals.append((start_m, end_m))
                    if e.section_id == section_b_id:
                        b_day_entries.append((start_m, e.title))
                except Exception:
                    pass

        b_day_entries.sort(key=lambda x: x[0])
        day_classes = []
        seen_titles = set()
        for _, title in b_day_entries:
            if title not in seen_titles:
                teacher_name = course_teacher_map.get(title, "Unknown")
                day_classes.append({'title': title, 'teacher_name': teacher_name})
                seen_titles.add(title)

        busy_intervals.sort(key=lambda x: x[0])
        merged = []
        for interval in busy_intervals:
            if not merged:
                merged.append([interval[0], interval[1]])
            else:
                prev = merged[-1]
                if interval[0] <= prev[1]:
                    prev[1] = max(prev[1], interval[1])
                else:
                    merged.append([interval[0], interval[1]])

        gaps = []
        current_time = DAY_START
        for start, end in merged:
            clp_ctime = max(current_time, DAY_START)
            clp_start = min(start, DAY_END)

            if clp_start > clp_ctime:
                gap_len = clp_start - clp_ctime
                if gap_len >= 15:
                    gaps.append((clp_ctime, clp_start, gap_len))

            current_time = max(current_time, end)

        clp_ctime = max(current_time, DAY_START)
        if clp_ctime < DAY_END:
            gap_len = DAY_END - clp_ctime
            if gap_len >= 15:
                gaps.append((clp_ctime, DAY_END, gap_len))

        if not gaps:
            free_slots_by_day.append({
                'day_name': DAYS_MAP[day_idx],
                'slots': [],
                'msg': "No common free time",
                'has_free': False,
                'classes': day_classes
            })
        else:
            if len(gaps) == 1 and gaps[0][0] == DAY_START and gaps[0][1] == DAY_END:
                msg = "All day free"
                has_free = True
                slots_formatted = []
            else:
                msg = ""
                has_free = True
                slots_formatted = [
                    {'text': f"{to_time_str(g[0])} - {to_time_str(g[1])}", 'duration': g[2]}
                    for g in gaps
                ]

            free_slots_by_day.append({
                'day_name': DAYS_MAP[day_idx],
                'slots': slots_formatted,
                'msg': msg,
                'has_free': has_free,
                'classes': day_classes
            })

    return free_slots_by_day


@timetable_bp.route('/manage', methods=['GET', 'POST'])
@school_scoped
@role_minimum('timetable_manager')
def manage_timetable():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_entry = TimetableEntry(
                section_id=request.form.get('section_id'),
                day=int(request.form.get('day')),
                start_time=request.form.get('start_time'),
                end_time=request.form.get('end_time'),
                title=request.form.get('title'),
                room=request.form.get('room'),
                color=request.form.get('color', 'var(--primary-color)')
            )
            section = Section.query.get(new_entry.section_id)
            if section and section.school_id == g.school_id:
                db.session.add(new_entry)
                db.session.commit()
                flash('Timetable entry added!', 'success')
            else:
                flash('Invalid section.', 'danger')
        elif action == 'delete':
            entry_id = request.form.get('entry_id')
            entry = TimetableEntry.query.get(entry_id)
            if entry and entry.section.school_id == g.school_id:
                db.session.delete(entry)
                db.session.commit()
                flash('Entry deleted.', 'info')

        return redirect(url_for('timetable.manage_timetable'))

    sections = Section.query.filter_by(school_id=g.school_id).all()
    entries = (
        TimetableEntry.query
        .join(Section)
        .filter(Section.school_id == g.school_id)
        .order_by(Section.code, TimetableEntry.day, TimetableEntry.start_time)
        .all()
    )
    return render_template('dashboard/manage_timetable.html', sections=sections, entries=entries)

from datetime import datetime
from ..models import (
    db, Section, Course, TimetableEntry, Announcement, Institution
)


def format_time_12hr(time_str):
    if not time_str:
        return ""
    time_str = time_str.strip()
    try:
        if ':' in time_str and 'AM' not in time_str.upper() and 'PM' not in time_str.upper():
            t = datetime.strptime(time_str[:5], "%H:%M")
            return t.strftime("%I:%M%p").lstrip('0')
    except Exception:
        pass
    return time_str.replace(" ", "")


def get_student_timetable_data(section_id, student_lab_section=None):
    timetable_data = {}
    for day_idx in range(6):
        entries = TimetableEntry.query.filter_by(
            section_id=section_id,
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
        timetable_data[day].sort(
            key=lambda x: datetime.strptime(
                x['startTime'].replace(" ", "").upper(), '%I:%M%p'
            ).time() if 'AM' in x['startTime'].upper() or 'PM' in x['startTime'].upper() else x['startTime']
        )

    return timetable_data


def get_teacher_timetable_data(teacher_id):
    entries = db.session.query(TimetableEntry, Course, Section)\
        .join(Course, TimetableEntry.course_id == Course.id)\
        .join(Section, TimetableEntry.section_id == Section.id)\
        .filter(Course.teacher_id == teacher_id)\
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
        timetable_data[day].sort(
            key=lambda x: datetime.strptime(
                x['start_time'].replace(" ", "").upper(), '%I:%M%p'
            ).time() if 'AM' in x['start_time'].upper() or 'PM' in x['start_time'].upper() else x['start_time']
        )

    hours = teaching_minutes // 60
    mins = teaching_minutes % 60
    teaching_hours_str = f"{hours}h {mins}m"

    return {
        'timetable_data': timetable_data,
        'total_classes': total_classes,
        'teaching_hours': teaching_hours_str,
        'sections_taught': sorted(list(sections_taught)),
    }


def get_system_timetable_data():
    all_entries = db.session.query(TimetableEntry, Section)\
        .join(Section, TimetableEntry.section_id == Section.id)\
        .order_by(TimetableEntry.day, TimetableEntry.start_time).all()
    return all_entries


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
        if display_h == 0:
            display_h = 12
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


def _create_announcement(institution_id, section_id, user_id, category, title, body):
    announcement = Announcement(
        institution_id=institution_id,
        section_id=section_id,
        teacher_id=user_id,
        category=category,
        title=title,
        body=body,
        posted_at=datetime.utcnow()
    )
    db.session.add(announcement)


def _day_name(day_idx):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    return days[day_idx] if 0 <= day_idx < 5 else "Unspecified Day"


def create_timetable_entry(section_id, day, start_time, end_time, subject,
                            teacher, room, period, color, institution_id, user_id):
    section = Section.query.get_or_404(section_id)
    if section.institution_id != institution_id:
        return None, "Invalid section"

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

    _create_announcement(
        institution_id, section_id, user_id, 'timetable',
        "New Class Added",
        f"New Class ({section.name}): {subject} added on {_day_name(day)} from {start_time} to {end_time} in {room} with {teacher}."
    )
    db.session.commit()

    return section_id, None


def update_timetable_entry(entry_id, new_subject, new_teacher, new_period,
                            new_room, new_start, new_end, institution_id, user_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    if institution_id and entry.section.institution_id != institution_id:
        return None, "Unauthorized"

    old_subject = entry.title
    old_room = entry.room
    old_teacher = entry.teacher

    day_name = _day_name(entry.day)

    if new_start:
        entry.start_time = new_start
    if new_end:
        entry.end_time = new_end

    if new_subject and new_subject != old_subject:
        entry.title = new_subject
        body = f"Timetable Update ({entry.section.name}): {day_name} {entry.start_time}-{entry.end_time} — '{old_subject}' has been changed to '{new_subject}'."
        _create_announcement(institution_id, entry.section_id, user_id, 'timetable', "Timetable Update", body)

    if new_room and new_room != old_room:
        entry.room = new_room
        body = f"Room Change ({entry.section.name}): {entry.title} on {day_name} {entry.start_time}-{entry.end_time} has moved from {old_room} to {new_room}."
        _create_announcement(institution_id, entry.section_id, user_id, 'timetable', "Room Change", body)

    if new_teacher and new_teacher != old_teacher:
        entry.teacher = new_teacher
        body = f"Teacher Change ({entry.section.name}): {entry.title} on {day_name} will now be taught by {new_teacher} instead of {old_teacher}."
        _create_announcement(institution_id, entry.section_id, user_id, 'timetable', "Teacher Change", body)

    entry.period = new_period
    db.session.commit()

    return entry.section_id, None


def cancel_timetable_entry(entry_id, institution_id, user_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    if entry.section.institution_id != institution_id:
        return None, "Unauthorized"

    entry.status = 'cancelled'
    db.session.commit()

    body = f"Class Cancelled (Section {entry.section.name}): {entry.title} on {_day_name(entry.day)} ({entry.start_time}-{entry.end_time}) has been cancelled."
    _create_announcement(institution_id, entry.section_id, user_id, 'timetable', "Class Cancelled", body)
    db.session.commit()

    return entry.section_id, None


def restore_timetable_entry(entry_id, institution_id, user_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    if entry.section.institution_id != institution_id:
        return None, "Unauthorized"

    entry.status = 'active'
    db.session.commit()

    body = f"Class Restored (Section {entry.section.name}): {entry.title} on {_day_name(entry.day)} ({entry.start_time}-{entry.end_time}) is back on schedule."
    _create_announcement(institution_id, entry.section_id, user_id, 'timetable', "Class Restored", body)
    db.session.commit()

    return entry.section_id, None


def delete_timetable_entry(entry_id, institution_id, user_id):
    entry = TimetableEntry.query.get_or_404(entry_id)
    if entry.section.institution_id != institution_id:
        return None, "Unauthorized"

    section_id = entry.section_id
    section_name = entry.section.name
    info = f"{entry.title} on {_day_name(entry.day)} ({entry.start_time}-{entry.end_time})"

    db.session.delete(entry)
    db.session.commit()

    body = f"Class Removed (Section {section_name}): {info} has been permanently removed from the timetable."
    _create_announcement(institution_id, section_id, user_id, 'timetable', "Class Removed", body)
    db.session.commit()

    return section_id, None


def manage_add_entry(section_id, day, start_time, end_time, title, room, color, institution_id):
    section = Section.query.get(section_id)
    if not section or section.institution_id != institution_id:
        return False, "Invalid section."
    new_entry = TimetableEntry(
        section_id=section_id,
        day=day,
        start_time=start_time,
        end_time=end_time,
        title=title,
        room=room,
        color=color,
    )
    db.session.add(new_entry)
    db.session.commit()
    return True, None


def manage_delete_entry(entry_id, institution_id):
    entry = TimetableEntry.query.get(entry_id)
    if not entry or entry.section.institution_id != institution_id:
        return False, "Invalid entry."
    db.session.delete(entry)
    db.session.commit()
    return True, None

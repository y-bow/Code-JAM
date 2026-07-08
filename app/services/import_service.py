import json
import os
import tempfile
import uuid
from io import StringIO
from datetime import datetime

import pandas as pd

from ..models import (
    db, User, Student, Teacher, Course, Section, Department, Enrollment,
    TimetableEntry, Club, Attendance, Grade, ImportBatch, get_setting, bcrypt
)
from ..models.auth import generate_username
from datetime import date


IMPORT_TYPES = [
    'students', 'faculty', 'courses', 'timetable', 'enrollments',
    'departments', 'sections', 'clubs', 'attendance', 'grades',
]

COLUMN_MAPS = {
    'students': {
        'required': ['name', 'email', 'section_code'],
        'optional': ['enrollment_year', 'major'],
    },
    'faculty': {
        'required': ['name', 'email', 'role'],
        'optional': ['department', 'office_hours'],
    },
    'courses': {
        'required': ['name', 'code', 'section_code', 'teacher_email', 'credits'],
        'optional': ['max_students', 'description'],
    },
    'timetable': {
        'required': ['section_code', 'day', 'start_time', 'end_time', 'course_code', 'room'],
        'optional': ['period_label', 'color'],
    },
    'enrollments': {
        'required': ['student_email', 'course_code'],
        'optional': ['status'],
    },
    'departments': {
        'required': ['name', 'code'],
        'optional': [],
    },
    'sections': {
        'required': ['name', 'code', 'department_code', 'batch_year'],
        'optional': [],
    },
    'clubs': {
        'required': ['name', 'category', 'contact_email'],
        'optional': ['description'],
    },
    'attendance': {
        'required': ['student_email', 'course_code', 'date', 'status'],
        'optional': [],
    },
    'grades': {
        'required': ['student_email', 'course_code', 'grade'],
        'optional': [],
    },
}


def parse_upload(file_storage):
    file_storage.seek(0)
    filename = file_storage.filename.lower()
    ext = os.path.splitext(filename)[1]

    try:
        if ext in ('.csv', '.tsv'):
            content = file_storage.read().decode('utf-8-sig')
            sep = '\t' if ext == '.tsv' else ','
            df = pd.read_csv(StringIO(content), sep=sep, dtype=str)
        elif ext in ('.xls', '.xlsx'):
            df = pd.read_excel(file_storage, dtype=str)
        else:
            return None, f'Unsupported file format: {ext}'
    except Exception as e:
        return None, f'Failed to parse file: {e}'

    df = df.fillna('')
    df = df.rename(columns=str.strip)
    columns = list(df.columns)
    rows = df.to_dict(orient='records')
    return {'columns': columns, 'rows': rows, 'total': len(rows)}, None


def detect_import_type(columns):
    col_lower = {c.lower().strip() for c in columns}
    best_type = None
    best_score = 0

    for imp_type, spec in COLUMN_MAPS.items():
        required = set(spec['required'])
        score = len(required & col_lower)
        if score > best_score:
            best_score = score
            best_type = imp_type

    return best_type


def validate_import(parsed, import_type, school_id):
    if import_type not in COLUMN_MAPS:
        return [], 'Invalid import type'

    spec = COLUMN_MAPS[import_type]
    required = set(spec['required'])
    all_expected = required | set(spec['optional'])
    col_lower = {c.lower().strip() for c in parsed['columns']}

    missing_required = required - col_lower
    if missing_required:
        return [], f'Missing required columns: {", ".join(sorted(missing_required))}'

    validated = []
    for idx, row in enumerate(parsed['rows']):
        errors = []
        row_data = {}

        for col in all_expected:
            val = ''
            for k, v in row.items():
                if k.lower().strip() == col.lower():
                    val = str(v).strip() if v else ''
                    break
            row_data[col] = val

        for req in required:
            if not row_data.get(req):
                errors.append(f'{req} is required')

        if import_type == 'students':
            _validate_student_row(row_data, school_id, errors)
        elif import_type == 'faculty':
            _validate_faculty_row(row_data, school_id, errors)
        elif import_type == 'courses':
            _validate_course_row(row_data, school_id, errors)
        elif import_type == 'timetable':
            _validate_timetable_row(row_data, school_id, errors)
        elif import_type == 'enrollments':
            _validate_enrollment_row(row_data, school_id, errors)
        elif import_type == 'departments':
            _validate_department_row(row_data, school_id, errors)
        elif import_type == 'sections':
            _validate_section_row(row_data, school_id, errors)
        elif import_type == 'clubs':
            _validate_club_row(row_data, school_id, errors)
        elif import_type == 'attendance':
            _validate_attendance_row(row_data, school_id, errors)
        elif import_type == 'grades':
            _validate_grade_row(row_data, school_id, errors)

        validated.append({
            'index': idx,
            'data': row_data,
            'errors': errors,
            'valid': len(errors) == 0,
        })

    return validated, None


def _validate_student_row(row, school_id, errors):
    email = row.get('email', '')
    if email and not _valid_email(email):
        errors.append(f'Invalid email: {email}')
    section_code = row.get('section_code', '')
    if section_code:
        section = Section.query.filter_by(school_id=school_id, code=section_code).first()
        if not section:
            errors.append(f'Section not found: {section_code}')
    enrollment_year = row.get('enrollment_year', '')
    if enrollment_year:
        try:
            int(enrollment_year)
        except ValueError:
            errors.append(f'Invalid enrollment_year: {enrollment_year}')


def _validate_faculty_row(row, school_id, errors):
    email = row.get('email', '')
    if email and not _valid_email(email):
        errors.append(f'Invalid email: {email}')
    role = row.get('role', '')
    valid_roles = ['professor', 'assistant_professor', 'dean']
    if role and role not in valid_roles:
        errors.append(f'Invalid role: {role}. Must be one of: {", ".join(valid_roles)}')


def _validate_course_row(row, school_id, errors):
    section_code = row.get('section_code', '')
    if section_code:
        section = Section.query.filter_by(school_id=school_id, code=section_code).first()
        if not section:
            errors.append(f'Section not found: {section_code}')
    teacher_email = row.get('teacher_email', '')
    if teacher_email:
        teacher = User.query.filter_by(school_id=school_id, email=teacher_email).first()
        if not teacher:
            errors.append(f'Teacher not found: {teacher_email}')
    credits = row.get('credits', '')
    if credits:
        try:
            int(credits)
        except ValueError:
            errors.append(f'Invalid credits: {credits}')


def _validate_timetable_row(row, school_id, errors):
    section_code = row.get('section_code', '')
    if section_code:
        section = Section.query.filter_by(school_id=school_id, code=section_code).first()
        if not section:
            errors.append(f'Section not found: {section_code}')
    day = row.get('day', '')
    if day:
        try:
            d = int(day)
            if d < 0 or d > 6:
                errors.append(f'Day must be 0-6 (Mon-Sun): {day}')
        except ValueError:
            errors.append(f'Invalid day: {day}')


def _validate_enrollment_row(row, school_id, errors):
    student_email = row.get('student_email', '')
    if student_email:
        student = User.query.filter_by(school_id=school_id, email=student_email, role='student').first()
        if not student:
            errors.append(f'Student not found: {student_email}')
    course_code = row.get('course_code', '')
    if course_code:
        course = Course.query.join(Section).filter(
            Section.school_id == school_id, Course.code == course_code
        ).first()
        if not course:
            errors.append(f'Course not found with code: {course_code}')


def _validate_department_row(row, school_id, errors):
    code = row.get('code', '')
    if code:
        existing = Department.query.filter_by(school_id=school_id, code=code).first()
        if existing:
            errors.append(f'Department with code {code} already exists')


def _validate_section_row(row, school_id, errors):
    department_code = row.get('department_code', '')
    if department_code:
        dept = Department.query.filter_by(school_id=school_id, code=department_code).first()
        if not dept:
            errors.append(f'Department not found: {department_code}')
    batch_year = row.get('batch_year', '')
    if batch_year:
        try:
            int(batch_year)
        except ValueError:
            errors.append(f'Invalid batch_year: {batch_year}')


def _validate_club_row(row, school_id, errors):
    contact_email = row.get('contact_email', '')
    if contact_email and not _valid_email(contact_email):
        errors.append(f'Invalid contact email: {contact_email}')
    name = row.get('name', '')
    if name:
        existing = Club.query.filter_by(school_id=school_id, name=name).first()
        if existing:
            errors.append(f'Club with name {name} already exists')


def _validate_attendance_row(row, school_id, errors):
    student_email = row.get('student_email', '')
    if student_email:
        student = User.query.filter_by(school_id=school_id, email=student_email, role='student').first()
        if not student:
            errors.append(f'Student not found: {student_email}')
    course_code = row.get('course_code', '')
    if course_code:
        course = Course.query.join(Section).filter(
            Section.school_id == school_id, Course.code == course_code
        ).first()
        if not course:
            errors.append(f'Course not found with code: {course_code}')
    status = row.get('status', '')
    valid_statuses = ['present', 'absent', 'late', 'excused']
    if status and status not in valid_statuses:
        errors.append(f'Invalid status: {status}. Must be one of: {", ".join(valid_statuses)}')
    date_val = row.get('date', '')
    if date_val:
        try:
            from datetime import datetime as dt
            dt.strptime(date_val, '%Y-%m-%d')
        except ValueError:
            errors.append(f'Invalid date format: {date_val}. Use YYYY-MM-DD')


def _validate_grade_row(row, school_id, errors):
    student_email = row.get('student_email', '')
    if student_email:
        student = User.query.filter_by(school_id=school_id, email=student_email, role='student').first()
        if not student:
            errors.append(f'Student not found: {student_email}')
    course_code = row.get('course_code', '')
    if course_code:
        course = Course.query.join(Section).filter(
            Section.school_id == school_id, Course.code == course_code
        ).first()
        if not course:
            errors.append(f'Course not found with code: {course_code}')
    grade = row.get('grade', '')
    if grade:
        try:
            float(grade)
        except ValueError:
            errors.append(f'Invalid grade value: {grade}')


def _valid_email(email):
    return '@' in email and '.' in email.split('@')[-1]


def execute_import(validated_rows, import_type, school_id, user_id):
    if import_type not in IMPORT_TYPES:
        return None, f'Invalid import type: {import_type}'

    valid_rows = [r for r in validated_rows if r['valid']]
    error_rows = [r for r in validated_rows if not r['valid']]

    if error_rows:
        error_details = [{'index': r['index'], 'errors': r['errors']} for r in error_rows]
        return None, f'Validation failed for {len(error_rows)} row(s). All rows must be valid.'

    if not valid_rows:
        return None, 'No rows to import'

    importer = _IMPORTERS.get(import_type)
    if not importer:
        return None, f'No importer for type: {import_type}'

    try:
        success_count = 0
        for row_data in valid_rows:
            success = importer(row_data['data'], school_id, user_id)
            if success:
                success_count += 1
            else:
                raise ValueError(f'Insertion failed for row {row_data["index"] + 1}')

        batch = ImportBatch(
            school_id=school_id,
            import_type=import_type,
            file_name=f'import_{import_type}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}',
            total_rows=len(validated_rows),
            success_count=success_count,
            error_count=0,
            errors_json=None,
            status='completed',
            created_by=user_id,
        )
        db.session.add(batch)
        db.session.commit()
        return batch, None
    except Exception as e:
        db.session.rollback()
        return None, f'Import failed: {e}'


def _import_student(row, school_id, user_id):
    email = row.get('email', '').strip().lower()
    existing = User.query.filter_by(school_id=school_id, email=email).first()
    if existing:
        return True

    section_code = row.get('section_code', '')
    section = Section.query.filter_by(school_id=school_id, code=section_code).first()
    if not section:
        return False

    default_password = get_setting('import.default_password', 'hive@1234')
    pw_hash = bcrypt.generate_password_hash(default_password).decode('utf-8')
    user = User(
        school_id=school_id,
        email=email,
        username=generate_username(email, school_id),
        password_hash=pw_hash,
        role='student',
        name=row.get('name', '').strip(),
        must_change_password=True,
    )
    db.session.add(user)
    db.session.flush()

    enrollment_year = row.get('enrollment_year', '')
    try:
        enrollment_year = int(enrollment_year) if enrollment_year else datetime.utcnow().year
    except ValueError:
        enrollment_year = datetime.utcnow().year

    student = Student(
        user_id=user.id,
        section_id=section.id,
        enrollment_year=enrollment_year,
        major=row.get('major', '').strip() or None,
    )
    db.session.add(student)
    return True


def _import_faculty(row, school_id, user_id):
    email = row.get('email', '').strip().lower()
    existing = User.query.filter_by(school_id=school_id, email=email).first()
    if existing:
        return True

    default_password = get_setting('import.default_password', 'hive@1234')
    pw_hash = bcrypt.generate_password_hash(default_password).decode('utf-8')
    user = User(
        school_id=school_id,
        email=email,
        username=generate_username(email, school_id),
        password_hash=pw_hash,
        role=row.get('role', 'professor').strip(),
        name=row.get('name', '').strip(),
        must_change_password=True,
    )
    db.session.add(user)
    db.session.flush()

    teacher = Teacher(
        user_id=user.id,
        department=row.get('department', '').strip() or None,
        office_hours=row.get('office_hours', '').strip() or None,
    )
    db.session.add(teacher)
    return True


def _import_course(row, school_id, user_id):
    code = row.get('code', '').strip()
    section_code = row.get('section_code', '').strip()
    section = Section.query.filter_by(school_id=school_id, code=section_code).first()
    if not section:
        return False

    existing = Course.query.filter_by(section_id=section.id, code=code).first()
    if existing:
        return True

    teacher_email = row.get('teacher_email', '').strip().lower()
    teacher = User.query.filter_by(school_id=school_id, email=teacher_email).first()
    if not teacher:
        return False

    try:
        credits = int(row.get('credits', 3))
    except ValueError:
        credits = 3

    max_students = None
    try:
        max_students = int(row.get('max_students', 0)) if row.get('max_students') else 50
    except ValueError:
        max_students = 50

    course = Course(
        section_id=section.id,
        name=row.get('name', '').strip(),
        code=code,
        teacher_id=teacher.id,
        credits=credits,
        max_students=max_students,
    )
    db.session.add(course)
    return True


def _import_timetable(row, school_id, user_id):
    section_code = row.get('section_code', '').strip()
    section = Section.query.filter_by(school_id=school_id, code=section_code).first()
    if not section:
        return False

    course_code = row.get('course_code', '').strip()
    course = Course.query.filter_by(section_id=section.id, code=course_code).first()

    day = int(row.get('day', 0))
    entry = TimetableEntry(
        section_id=section.id,
        course_id=course.id if course else None,
        day=day,
        start_time=row.get('start_time', '').strip(),
        end_time=row.get('end_time', '').strip(),
        title=row.get('course_code', '').strip() or 'Class',
        teacher=row.get('teacher', '').strip() or None,
        room=row.get('room', '').strip(),
        period=row.get('period_label', '').strip() or None,
        color=row.get('color', 'var(--primary-color)').strip(),
    )
    db.session.add(entry)
    return True


def _import_enrollment(row, school_id, user_id):
    student_email = row.get('student_email', '').strip().lower()
    student = User.query.filter_by(school_id=school_id, email=student_email, role='student').first()
    if not student:
        return False

    course_code = row.get('course_code', '').strip()
    course = Course.query.join(Section).filter(
        Section.school_id == school_id, Course.code == course_code
    ).first()
    if not course:
        return False

    existing = Enrollment.query.filter_by(
        student_id=student.id, course_id=course.id
    ).first()
    if existing:
        existing.status = row.get('status', 'active').strip() or 'active'
        return True

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status=row.get('status', 'active').strip() or 'active',
    )
    db.session.add(enrollment)
    return True


def _import_department(row, school_id, user_id):
    code = row.get('code', '').strip()
    existing = Department.query.filter_by(school_id=school_id, code=code).first()
    if existing:
        return True
    dept = Department(
        school_id=school_id,
        name=row.get('name', '').strip(),
        code=code,
    )
    db.session.add(dept)
    return True


def _import_section(row, school_id, user_id):
    code = row.get('code', '').strip()
    existing = Section.query.filter_by(school_id=school_id, code=code).first()
    if existing:
        return True
    department_code = row.get('department_code', '').strip()
    dept = Department.query.filter_by(school_id=school_id, code=department_code).first()
    if not dept:
        return False
    try:
        batch_year = int(row.get('batch_year', datetime.utcnow().year))
    except ValueError:
        batch_year = datetime.utcnow().year
    section = Section(
        school_id=school_id,
        department_id=dept.id,
        name=row.get('name', '').strip(),
        code=code,
        batch_year=batch_year,
    )
    db.session.add(section)
    return True


def _import_club(row, school_id, user_id):
    name = row.get('name', '').strip()
    existing = Club.query.filter_by(school_id=school_id, name=name).first()
    if existing:
        return True
    club = Club(
        school_id=school_id,
        name=name,
        category=row.get('category', '').strip(),
        contact_email=row.get('contact_email', '').strip(),
        description=row.get('description', '').strip() or None,
    )
    db.session.add(club)
    return True


def _import_attendance(row, school_id, user_id):
    student_email = row.get('student_email', '').strip().lower()
    student = User.query.filter_by(school_id=school_id, email=student_email, role='student').first()
    if not student:
        return False
    course_code = row.get('course_code', '').strip()
    course = Course.query.join(Section).filter(
        Section.school_id == school_id, Course.code == course_code
    ).first()
    if not course:
        return False
    try:
        att_date = datetime.strptime(row.get('date', '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return False
    existing = Attendance.query.filter_by(
        course_id=course.id, student_id=student.id, date=att_date
    ).first()
    if existing:
        existing.status = row.get('status', 'present').strip()
        return True
    record = Attendance(
        course_id=course.id,
        student_id=student.id,
        date=att_date,
        status=row.get('status', 'present').strip(),
    )
    db.session.add(record)
    return True


def _import_grade(row, school_id, user_id):
    student_email = row.get('student_email', '').strip().lower()
    student = User.query.filter_by(school_id=school_id, email=student_email, role='student').first()
    if not student:
        return False
    course_code = row.get('course_code', '').strip()
    course = Course.query.join(Section).filter(
        Section.school_id == school_id, Course.code == course_code
    ).first()
    if not course:
        return False
    try:
        grade_val = float(row.get('grade', 0))
    except ValueError:
        return False
    existing = Grade.query.filter_by(student_id=student.id, course_id=course.id).first()
    if existing:
        existing.grade = grade_val
        return True
    grade = Grade(
        student_id=student.id,
        course_id=course.id,
        grade=grade_val,
    )
    db.session.add(grade)
    if student.student_profile:
        student.student_profile.cgpa = grade_val
    return True


_IMPORTERS = {
    'students': _import_student,
    'faculty': _import_faculty,
    'courses': _import_course,
    'timetable': _import_timetable,
    'enrollments': _import_enrollment,
    'departments': _import_department,
    'sections': _import_section,
    'clubs': _import_club,
    'attendance': _import_attendance,
    'grades': _import_grade,
}


def get_recent_batches(school_id, limit=10):
    return ImportBatch.query.filter_by(school_id=school_id).order_by(
        ImportBatch.created_at.desc()
    ).limit(limit).all()

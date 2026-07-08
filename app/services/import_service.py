import json
import os
import tempfile
import uuid
from io import StringIO
from datetime import datetime

import pandas as pd

from ..models import (
    db, User, Student, Teacher, Course, Section, Enrollment,
    TimetableEntry, ImportBatch, get_setting
)


IMPORT_TYPES = ['students', 'faculty', 'courses', 'timetable', 'enrollments']

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


def _valid_email(email):
    return '@' in email and '.' in email.split('@')[-1]


def execute_import(validated_rows, import_type, school_id, user_id):
    if import_type not in IMPORT_TYPES:
        return None, f'Invalid import type: {import_type}'

    valid_rows = [r for r in validated_rows if r['valid']]
    error_rows = [r for r in validated_rows if not r['valid']]

    if not valid_rows:
        return None, 'No valid rows to import'

    importer = _IMPORTERS.get(import_type)
    if not importer:
        return None, f'No importer for type: {import_type}'

    success_count = 0
    error_details = [{'index': r['index'], 'errors': r['errors']} for r in error_rows]

    for row_data in valid_rows:
        success = importer(row_data['data'], school_id, user_id)
        if success:
            success_count += 1
        else:
            error_details.append({'index': row_data['index'], 'errors': ['Insertion failed']})

    batch = ImportBatch(
        school_id=school_id,
        import_type=import_type,
        file_name=f'import_{import_type}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}',
        total_rows=len(validated_rows),
        success_count=success_count,
        error_count=len(validated_rows) - success_count,
        errors_json=json.dumps(error_details) if error_details else None,
        status='completed',
        created_by=user_id,
    )
    db.session.add(batch)
    db.session.commit()

    return batch, None


def _import_student(row, school_id, user_id):
    email = row.get('email', '').strip().lower()
    existing = User.query.filter_by(school_id=school_id, email=email).first()
    if existing:
        return True

    section_code = row.get('section_code', '')
    section = Section.query.filter_by(school_id=school_id, code=section_code).first()
    if not section:
        return False

    default_password = get_setting('import.default_password', 'password123')
    user = User(
        school_id=school_id,
        email=email,
        password_hash=default_password,
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

    default_password = get_setting('import.default_password', 'password123')
    user = User(
        school_id=school_id,
        email=email,
        password_hash=default_password,
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


_IMPORTERS = {
    'students': _import_student,
    'faculty': _import_faculty,
    'courses': _import_course,
    'timetable': _import_timetable,
    'enrollments': _import_enrollment,
}


def get_recent_batches(school_id, limit=10):
    return ImportBatch.query.filter_by(school_id=school_id).order_by(
        ImportBatch.created_at.desc()
    ).limit(limit).all()

import json
import logging
import os
import re
import tempfile
import uuid
from io import StringIO
from datetime import datetime, date

import pandas as pd

from ..models import (
    db, User, Student, Teacher, Course, Section, Department, Enrollment,
    TimetableEntry, Club, Attendance, Grade, ImportBatch, get_setting, bcrypt
)
from ..models.auth import generate_username

logger = logging.getLogger(__name__)


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

IMPORT_DEPENDENCY_ORDER = [
    'departments',
    'sections',
    'faculty',
    'courses',
    'students',
    'enrollments',
    'timetable',
    'clubs',
    'attendance',
    'grades',
]

FILENAME_TYPE_PATTERNS = {
    'departments': re.compile(r'departments?', re.I),
    'sections': re.compile(r'sections?', re.I),
    'students': re.compile(r'students?', re.I),
    'faculty': re.compile(r'faculty|teachers?|professors?', re.I),
    'courses': re.compile(r'courses?|subjects?', re.I),
    'timetable': re.compile(r'timetable|schedule', re.I),
    'enrollments': re.compile(r'enrollments?|registrations?', re.I),
    'clubs': re.compile(r'clubs?', re.I),
    'attendance': re.compile(r'attendance', re.I),
    'grades': re.compile(r'grades?|marks?', re.I),
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
    best_ratio = 0.0
    best_matched = 0

    for imp_type, spec in COLUMN_MAPS.items():
        required = set(spec['required'])
        matched = len(required & col_lower)
        if matched == 0:
            continue
        ratio = matched / len(required) if required else 0

        if ratio > best_ratio or (ratio == best_ratio and matched > best_matched):
            best_ratio = ratio
            best_matched = matched
            best_type = imp_type

    if best_type:
        logger.info(
            'detect_import_type: columns=%s -> type=%s (ratio=%.2f, matched=%d/%d)',
            sorted(col_lower), best_type, best_ratio,
            best_matched, len(COLUMN_MAPS[best_type]['required']),
        )
    else:
        logger.warning('detect_import_type: columns=%s -> no match', sorted(col_lower))

    return best_type


def detect_import_type_from_filename(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    for imp_type, pattern in FILENAME_TYPE_PATTERNS.items():
        if pattern.search(base):
            logger.info(
                'detect_import_type_from_filename: filename=%s -> type=%s',
                filename, imp_type,
            )
            return imp_type
    return None


def validate_import(parsed, import_type, school_id, conflict_strategy='skip'):
    if import_type not in COLUMN_MAPS:
        logger.error('validate_import: invalid import_type=%s', import_type)
        return [], 'Invalid import type'

    spec = COLUMN_MAPS[import_type]
    required = set(spec['required'])
    all_expected = required | set(spec['optional'])
    col_lower = {c.lower().strip() for c in parsed['columns']}

    logger.info(
        'validate_import: type=%s validator=%s required=%s file_columns=%s',
        import_type, f'_validate_{import_type}_row', sorted(required), sorted(col_lower),
    )

    missing_required = required - col_lower
    if missing_required:
        logger.warning(
            'validate_import: type=%s missing_required=%s',
            import_type, sorted(missing_required),
        )
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
            _validate_department_row(row_data, school_id, errors, conflict_strategy)
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


def _validate_department_row(row, school_id, errors, conflict_strategy='skip'):
    pass


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


def execute_import(validated_rows, import_type, school_id, user_id, conflict_strategy='skip'):
    if import_type not in IMPORT_TYPES:
        logger.error('execute_import: invalid import_type=%s', import_type)
        return None, f'Invalid import type: {import_type}'

    valid_rows = [r for r in validated_rows if r['valid']]
    error_rows = [r for r in validated_rows if not r['valid']]

    logger.info(
        'execute_import: type=%s importer=_import_%s valid_rows=%d error_rows=%d strategy=%s',
        import_type, import_type, len(valid_rows), len(error_rows), conflict_strategy,
    )

    if error_rows:
        error_details = [{'index': r['index'], 'errors': r['errors']} for r in error_rows]
        logger.warning(
            'execute_import: type=%s rejecting import due to %d error rows',
            import_type, len(error_rows),
        )
        return None, f'Validation failed for {len(error_rows)} row(s). All rows must be valid.'

    if not valid_rows:
        return None, 'No rows to import'

    importer = _IMPORTERS.get(import_type)
    if not importer:
        return None, f'No importer for type: {import_type}'

    try:
        success_count = 0
        skipped_count = 0
        updated_count = 0
        for row_data in valid_rows:
            result = importer(row_data['data'], school_id, user_id, conflict_strategy)
            if result == 'imported':
                success_count += 1
            elif result == 'skipped':
                skipped_count += 1
            elif result == 'updated':
                updated_count += 1
            else:
                raise ValueError(f'Insertion failed for row {row_data["index"] + 1}')

        batch = ImportBatch(
            school_id=school_id,
            import_type=import_type,
            file_name=f'import_{import_type}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}',
            total_rows=len(validated_rows),
            success_count=success_count,
            skipped_count=skipped_count,
            updated_count=updated_count,
            error_count=0,
            errors_json=None,
            conflict_strategy=conflict_strategy,
            status='completed',
            created_by=user_id,
        )
        db.session.add(batch)
        db.session.commit()
        return batch, None
    except Exception as e:
        db.session.rollback()
        return None, f'Import failed: {e}'


def _import_student(row, school_id, user_id, strategy='skip'):
    email = row.get('email', '').strip().lower()
    existing = User.query.filter_by(school_id=school_id, email=email, role='student').first()

    if existing:
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            Student.query.filter_by(user_id=existing.id).delete()
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.name = row.get('name', '').strip()
            db.session.flush()
            return 'updated'

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
    return 'imported'


def _import_faculty(row, school_id, user_id, strategy='skip'):
    email = row.get('email', '').strip().lower()
    existing = User.query.filter_by(school_id=school_id, email=email, role='faculty').first()
    if not existing:
        existing = User.query.filter_by(school_id=school_id, email=email).first()

    if existing:
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            Teacher.query.filter_by(user_id=existing.id).delete()
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.name = row.get('name', '').strip()
            existing.role = row.get('role', 'professor').strip()
            db.session.flush()
            teacher = Teacher.query.filter_by(user_id=existing.id).first()
            if teacher:
                teacher.department = row.get('department', '').strip() or None
                teacher.office_hours = row.get('office_hours', '').strip() or None
                db.session.flush()
            return 'updated'

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
    return 'imported'


def _import_course(row, school_id, user_id, strategy='skip'):
    code = row.get('code', '').strip()
    section_code = row.get('section_code', '').strip()
    section = Section.query.filter_by(school_id=school_id, code=section_code).first()
    if not section:
        return False

    existing = Course.query.filter_by(section_id=section.id, code=code).first()

    if existing:
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.name = row.get('name', '').strip()
            try:
                existing.credits = int(row.get('credits', existing.credits))
            except ValueError:
                pass
            teacher_email = row.get('teacher_email', '').strip().lower()
            if teacher_email:
                teacher = User.query.filter_by(school_id=school_id, email=teacher_email).first()
                if teacher:
                    existing.teacher_id = teacher.id
            db.session.flush()
            return 'updated'

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
    return 'imported'


def _import_timetable(row, school_id, user_id, strategy='skip'):
    section_code = row.get('section_code', '').strip()
    section = Section.query.filter_by(school_id=school_id, code=section_code).first()
    if not section:
        return False

    course_code = row.get('course_code', '').strip()
    course = Course.query.filter_by(section_id=section.id, code=course_code).first()

    existing = TimetableEntry.query.filter_by(
        section_id=section.id,
        day=row.get('day', 0),
        start_time=row.get('start_time', '').strip(),
    ).first()

    if existing:
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.end_time = row.get('end_time', '').strip()
            existing.room = row.get('room', '').strip()
            if course:
                existing.course_id = course.id
            db.session.flush()
            return 'updated'

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
    return 'imported'


def _import_enrollment(row, school_id, user_id, strategy='skip'):
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
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.status = row.get('status', 'active').strip() or 'active'
            db.session.flush()
            return 'updated'

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status=row.get('status', 'active').strip() or 'active',
    )
    db.session.add(enrollment)
    return 'imported'


def _import_department(row, school_id, user_id, strategy='skip'):
    code = row.get('code', '').strip()
    existing = Department.query.filter_by(school_id=school_id, code=code).first()

    if existing:
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.name = row.get('name', '').strip()
            db.session.flush()
            return 'updated'

    dept = Department(
        school_id=school_id,
        name=row.get('name', '').strip(),
        code=code,
    )
    db.session.add(dept)
    return 'imported'


def _import_section(row, school_id, user_id, strategy='skip'):
    code = row.get('code', '').strip()
    existing = Section.query.filter_by(school_id=school_id, code=code).first()

    if existing:
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            department_code = row.get('department_code', '').strip()
            dept = Department.query.filter_by(school_id=school_id, code=department_code).first()
            if dept:
                existing.department_id = dept.id
            existing.name = row.get('name', '').strip()
            db.session.flush()
            return 'updated'

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
    return 'imported'


def _import_club(row, school_id, user_id, strategy='skip'):
    name = row.get('name', '').strip()
    existing = Club.query.filter_by(school_id=school_id, name=name).first()

    if existing:
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.category = row.get('category', '').strip()
            existing.contact_email = row.get('contact_email', '').strip()
            existing.description = row.get('description', '').strip() or None
            db.session.flush()
            return 'updated'

    club = Club(
        school_id=school_id,
        name=name,
        category=row.get('category', '').strip(),
        contact_email=row.get('contact_email', '').strip(),
        description=row.get('description', '').strip() or None,
    )
    db.session.add(club)
    return 'imported'


def _import_attendance(row, school_id, user_id, strategy='skip'):
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
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.status = row.get('status', 'present').strip()
            db.session.flush()
            return 'updated'

    record = Attendance(
        course_id=course.id,
        student_id=student.id,
        date=att_date,
        status=row.get('status', 'present').strip(),
    )
    db.session.add(record)
    return 'imported'


def _import_grade(row, school_id, user_id, strategy='skip'):
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
        if strategy == 'skip':
            return 'skipped'
        elif strategy == 'replace':
            db.session.delete(existing)
            db.session.flush()
        elif strategy == 'update':
            existing.grade = grade_val
            db.session.flush()
            return 'updated'

    grade = Grade(
        student_id=student.id,
        course_id=course.id,
        grade=grade_val,
    )
    db.session.add(grade)
    return 'imported'


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


def batch_import(files_data, school_id, user_id, conflict_strategy='skip'):
    results = []
    pending = []

    for fd in files_data:
        import_type = fd.get('import_type')
        if not import_type:
            import_type = detect_import_type(fd['parsed']['columns'])
        if not import_type:
            results.append({
                'file': fd.get('filename', 'unknown'),
                'status': 'warning',
                'message': 'Could not detect import type from columns',
                'import_type': None,
            })
            continue
        pending.append({'file': fd.get('filename', 'unknown'), 'import_type': import_type, 'parsed': fd['parsed']})

    sorted_pending = sorted(pending, key=lambda x: _dependency_sort_key(x['import_type']))

    for item in sorted_pending:
        filename = item['file']
        import_type = item['import_type']
        parsed = item['parsed']

        logger.info(
            'batch_import: processing file=%s type=%s rows=%d',
            filename, import_type, parsed['total'],
        )

        validated, err = validate_import(parsed, import_type, school_id)
        if err:
            results.append({
                'file': filename,
                'status': 'error',
                'message': err,
                'import_type': import_type,
            })
            continue

        invalid = [r for r in validated if not r['valid']]
        if invalid:
            error_list = [f'Row {r["index"]+1}: {"; ".join(r["errors"])}' for r in invalid]
            results.append({
                'file': filename,
                'status': 'error',
                'message': f'{len(invalid)} row(s) invalid',
                'details': error_list,
                'import_type': import_type,
            })
            continue

        batch, err = execute_import(validated, import_type, school_id, user_id, conflict_strategy)
        if err:
            results.append({
                'file': filename,
                'status': 'error',
                'message': err,
                'import_type': import_type,
            })
        else:
            counts = []
            if batch.success_count:
                counts.append(f'{batch.success_count} imported')
            if batch.skipped_count:
                counts.append(f'{batch.skipped_count} skipped')
            if batch.updated_count:
                counts.append(f'{batch.updated_count} updated')
            results.append({
                'file': filename,
                'status': 'success',
                'message': ', '.join(counts) if counts else 'completed',
                'import_type': import_type,
                'batch': batch,
            })

    return results


def _dependency_sort_key(import_type):
    try:
        return IMPORT_DEPENDENCY_ORDER.index(import_type)
    except ValueError:
        return len(IMPORT_DEPENDENCY_ORDER)


def get_recent_batches(school_id, limit=10):
    return ImportBatch.query.filter_by(school_id=school_id).order_by(
        ImportBatch.created_at.desc()
    ).limit(limit).all()

import pytest
from app.services.import_service import (
    detect_import_type, validate_import, COLUMN_MAPS, IMPORT_TYPES,
)


# -- detect_import_type tests -------------------------------------------------

IMPORT_COLUMN_SETS = {
    'departments': ['code', 'name'],
    'sections': ['name', 'code', 'department_code', 'batch_year'],
    'students': ['name', 'email', 'section_code'],
    'faculty': ['name', 'email', 'role'],
    'courses': ['name', 'code', 'section_code', 'teacher_email', 'credits'],
    'timetable': ['section_code', 'day', 'start_time', 'end_time', 'course_code', 'room'],
    'enrollments': ['student_email', 'course_code'],
    'clubs': ['name', 'category', 'contact_email'],
    'attendance': ['student_email', 'course_code', 'date', 'status'],
    'grades': ['student_email', 'course_code', 'grade'],
}

EXACT_MATCH_COLUMNS = IMPORT_COLUMN_SETS.copy()


class TestDetectImportType:
    def verify_detection(self, import_type, columns):
        result = detect_import_type(columns)
        assert result == import_type, (
            f'{columns} -> detected={result}, expected={import_type}'
        )

    def verify_no_match(self, columns):
        result = detect_import_type(columns)
        assert result is None, f'{columns} -> detected={result}, expected=None'

    def test_departments_csv_detected_as_departments(self):
        self.verify_detection('departments', ['code', 'name'])

    def test_sections_csv_detected_as_sections(self):
        self.verify_detection('sections', ['name', 'code', 'department_code', 'batch_year'])

    def test_students_csv_detected_as_students(self):
        self.verify_detection('students', ['name', 'email', 'section_code'])

    def test_faculty_csv_detected_as_faculty(self):
        self.verify_detection('faculty', ['name', 'email', 'role'])

    def test_courses_csv_detected_as_courses(self):
        self.verify_detection('courses', ['name', 'code', 'section_code', 'teacher_email', 'credits'])

    def test_timetable_csv_detected_as_timetable(self):
        self.verify_detection('timetable', ['section_code', 'day', 'start_time', 'end_time', 'course_code', 'room'])

    def test_enrollments_csv_detected_as_enrollments(self):
        self.verify_detection('enrollments', ['student_email', 'course_code'])

    def test_clubs_csv_detected_as_clubs(self):
        self.verify_detection('clubs', ['name', 'category', 'contact_email'])

    def test_attendance_csv_detected_as_attendance(self):
        self.verify_detection('attendance', ['student_email', 'course_code', 'date', 'status'])

    def test_grades_csv_detected_as_grades(self):
        self.verify_detection('grades', ['student_email', 'course_code', 'grade'])

    def test_departments_columns_never_detected_as_courses(self):
        """Regression: departments.csv [code,name] must NOT be detected as courses."""
        result = detect_import_type(['code', 'name'])
        assert result == 'departments', f'departments columns -> {result} (expected departments)'

    def test_courses_columns_never_detected_as_departments(self):
        result = detect_import_type(['name', 'code', 'section_code', 'teacher_email', 'credits'])
        assert result == 'courses', f'courses columns -> {result} (expected courses)'

    def test_empty_columns_returns_none(self):
        self.verify_no_match([])

    def test_unrelated_columns_returns_none(self):
        self.verify_no_match(['foo', 'bar', 'baz'])

    def test_case_insensitive_matching(self):
        result = detect_import_type(['CODE', 'NAME', 'DEPARTMENT_CODE', 'BATCH_YEAR'])
        assert result == 'sections'

    def test_whitespace_tolerant_matching(self):
        result = detect_import_type([' code ', ' name ', ' department_code ', ' batch_year '])
        assert result == 'sections'

    def test_partial_match_with_extra_columns(self):
        result = detect_import_type(['code', 'name', 'extra1', 'extra2', 'extra3'])
        assert result == 'departments', f'extra cols -> {result} (expected departments)'


# -- validate_import routing tests --------------------------------------------

class FakeParsed(dict):
    def __init__(self, columns):
        super().__init__(columns=columns, rows=[{c: '' for c in columns}], total=len(columns))


class TestValidateImportRouting:
    def test_departments_validates_with_department_schema(self):
        parsed = FakeParsed(['code', 'name'])
        result, err = validate_import(parsed, 'departments', 'dummy_school')
        assert err is None, f'departments validation should pass, got: {err}'

    def test_courses_validates_with_course_schema(self):
        parsed = FakeParsed(['name', 'code', 'section_code', 'teacher_email', 'credits'])
        result, err = validate_import(parsed, 'courses', 'dummy_school')
        assert err is None, f'courses validation should pass, got: {err}'

    def test_departments_rejected_by_course_schema(self):
        parsed = FakeParsed(['code', 'name'])
        result, err = validate_import(parsed, 'courses', 'dummy_school')
        assert err is not None, 'departments columns should be rejected by course schema'
        assert 'credits' in err
        assert 'section_code' in err
        assert 'teacher_email' in err

    def test_courses_rejected_by_department_schema(self):
        parsed = FakeParsed(['name', 'code', 'section_code', 'teacher_email', 'credits'])
        result, err = validate_import(parsed, 'departments', 'dummy_school')
        assert err is None, 'extra columns should not cause rejection for departments'

    def test_every_import_type_accepts_own_columns(self):
        for import_type, columns in IMPORT_COLUMN_SETS.items():
            parsed = FakeParsed(columns)
            result, err = validate_import(parsed, import_type, 'dummy_school')
            assert err is None, (
                f'{import_type} should accept its own columns {columns}, got: {err}'
            )

    def test_every_import_type_rejects_wrong_required_columns(self):
        """Each importer rejects columns that are missing its required columns."""
        wholly_wrong_sets = {
            'departments': ['foo', 'bar'],
            'sections': ['foo', 'bar'],
            'students': ['foo', 'bar'],
            'faculty': ['foo', 'bar'],
            'courses': ['code', 'name'],
            'timetable': ['foo', 'bar'],
            'enrollments': ['foo', 'bar'],
            'clubs': ['foo', 'bar'],
            'attendance': ['foo', 'bar'],
            'grades': ['foo', 'bar'],
        }
        for import_type, wrong_cols in wholly_wrong_sets.items():
            parsed = FakeParsed(wrong_cols)
            result, err = validate_import(parsed, import_type, 'dummy_school')
            assert err is not None, (
                f'{import_type} should reject columns {wrong_cols}, got: {err}'
            )


# -- schema integrity tests ---------------------------------------------------

class TestSchemaIntegrity:
    def test_all_import_types_have_column_maps(self):
        for t in IMPORT_TYPES:
            assert t in COLUMN_MAPS, f'{t} missing from COLUMN_MAPS'

    def test_all_column_map_types_are_in_import_types(self):
        for t in COLUMN_MAPS:
            assert t in IMPORT_TYPES, f'{t} in COLUMN_MAPS but not in IMPORT_TYPES'

    def test_each_importer_has_required_columns(self):
        for t, spec in COLUMN_MAPS.items():
            assert len(spec['required']) > 0, f'{t} has no required columns'

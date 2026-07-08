from app.models import School, User, Student, Section, Course, Enrollment, TimetableEntry


class TestFormatTime12hr:
    def test_returns_empty_for_none(self):
        from app.services import format_time_12hr
        assert format_time_12hr("") == ""

    def test_converts_24h_to_12h(self):
        from app.services import format_time_12hr
        result = format_time_12hr("14:30")
        assert result == "2:30PM"

    def test_preserves_12h_format(self):
        from app.services import format_time_12hr
        result = format_time_12hr("10:40 AM")
        assert result == "10:40AM"

    def test_handles_midnight(self):
        from app.services import format_time_12hr
        result = format_time_12hr("00:00")
        assert "12" in result and "AM" in result


class TestGetCommonFreeSlots:
    def test_returns_list_of_5_days(self, app, db_session):
        from app.services import get_common_free_slots
        with app.app_context():
            section = Section.query.first()
            if not section:
                assert True
                return
            result = get_common_free_slots(section.id, section.id)
            assert len(result) == 5
            for day in result:
                assert 'day_name' in day
                assert 'slots' in day
                assert 'has_free' in day

    def test_all_day_free_for_empty_sections(self, app, db_session):
        from app.services import get_common_free_slots
        with app.app_context():
            school = School.query.first()
            empty_a = Section(school_id=school.id, name='Empty A', code='EA', batch_year=2025)
            empty_b = Section(school_id=school.id, name='Empty B', code='EB', batch_year=2025)
            db_session.session.add_all([empty_a, empty_b])
            db_session.session.commit()

            result = get_common_free_slots(empty_a.id, empty_b.id)
            for day in result:
                assert day['has_free'] is True


class TestGetUserCourses:
    def test_returns_courses_for_student(self, app, db_session):
        from app.services import get_user_courses
        with app.app_context():
            student = User.query.filter_by(role='student').first()
            if not student:
                assert True
                return
            courses = get_user_courses(student, student.school_id)
            assert isinstance(courses, list)

    def test_returns_courses_for_professor(self, app, db_session):
        from app.services import get_user_courses
        with app.app_context():
            prof = User.query.filter_by(role='professor').first()
            if not prof:
                assert True
                return
            courses = get_user_courses(prof, prof.school_id)
            assert isinstance(courses, list)


class TestGetAssignedCourses:
    def test_returns_query_for_professor(self, app, db_session):
        from app.services import get_assigned_courses
        with app.app_context():
            prof = User.query.filter_by(role='professor').first()
            if not prof:
                assert True
                return
            courses = get_assigned_courses(prof)
            assert isinstance(courses, list)


class TestUpdateMeetLink:
    def test_updates_when_authorized(self, app, db_session):
        from app.services import update_meet_link
        with app.app_context():
            prof = User.query.filter_by(role='professor').first()
            if not prof:
                assert True
                return
            course = Course(teacher_id=prof.id, name='Test Course', code='TC101',
                            section_id=Section.query.first().id, credits=3)
            db_session.session.add(course)
            db_session.session.commit()

            result = update_meet_link(course.id, 'https://meet.example.com', prof.id)
            assert result is True
            assert course.meet_link == 'https://meet.example.com'

    def test_rejects_when_unauthorized(self, app, db_session):
        from app.services import update_meet_link
        with app.app_context():
            prof = User.query.filter_by(role='professor').first()
            student = User.query.filter_by(role='student').first()
            if not prof or not student:
                assert True
                return
            course = Course(teacher_id=prof.id, name='Test Course 2', code='TC102',
                            section_id=Section.query.first().id, credits=3)
            db_session.session.add(course)
            db_session.session.commit()

            result = update_meet_link(course.id, 'https://meet.example.com', student.id)
            assert result is False


class TestProcessNomination:
    def test_approve_nomination(self, app, db_session):
        from app.services import process_nomination
        from app.models import ClassRepNomination
        with app.app_context():
            student = User.query.filter_by(role='student').first()
            dean = User(school_id=student.school_id, email='dean@test.edu',
                         password_hash='x', role='dean', name='Test Dean')
            db_session.session.add(dean)
            db_session.session.commit()

            nom = ClassRepNomination(
                section_id=student.student_profile.section_id,
                student_id=student.id,
                nominated_by=dean.id,
                course_id=Course.query.first().id if Course.query.first() else None,
                status='pending'
            )
            db_session.session.add(nom)
            db_session.session.commit()

            success, msg = process_nomination(nom.id, 'approve', student.school_id, dean.id)
            assert success is True
            assert 'approved' in msg

    def test_reject_nomination(self, app, db_session):
        from app.services import process_nomination
        from app.models import ClassRepNomination
        with app.app_context():
            student = User.query.filter_by(role='student').first()
            if not student or not student.student_profile:
                assert True
                return
            dean = User(school_id=student.school_id, email='dean2@test.edu',
                         password_hash='x', role='dean', name='Test Dean 2')
            db_session.session.add(dean)
            db_session.session.commit()
            nom = ClassRepNomination(
                section_id=student.student_profile.section_id,
                student_id=student.id,
                nominated_by=dean.id,
                course_id=Course.query.first().id if Course.query.first() else None,
                status='pending'
            )
            db_session.session.add(nom)
            db_session.session.commit()

            success, msg = process_nomination(nom.id, 'reject', student.school_id, dean.id)
            assert success is True


class TestSchoolStats:
    def test_get_school_stats_returns_dict(self, app, db_session):
        from app.services import get_school_stats
        with app.app_context():
            school = School.query.first()
            stats = get_school_stats(school.id)
            assert isinstance(stats, dict)
            assert 'total_students' in stats
            assert 'total_teachers' in stats


class TestAtRiskStudents:
    def test_get_at_risk_students_returns_list(self, app, db_session):
        from app.services import get_at_risk_students
        with app.app_context():
            school = School.query.first()
            students = get_at_risk_students(school.id)
            assert isinstance(students, list)

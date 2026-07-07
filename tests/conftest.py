import os
import tempfile
import pytest
from app import create_app, db

@pytest.fixture(scope='session')
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['WTF_CSRF_ENABLED'] = 'False'

    _app = create_app()
    _app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
    })

    with _app.app_context():
        from flask_migrate import upgrade
        upgrade()
        _seed_test_data()

    yield _app

    os.close(db_fd)
    try:
        os.unlink(db_path)
    except PermissionError:
        pass


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        yield db


def _seed_test_data():
    from app import bcrypt
    from app.models import School, User, Student, Section

    school = School(name='Test University', code='TU', domain='test.edu')
    db.session.add(school)
    db.session.commit()

    section = Section(school_id=school.id, name='Section A', code='TU-CS-S1', batch_year=2025)
    db.session.add(section)
    db.session.commit()

    pw = bcrypt.generate_password_hash('test1234').decode('utf-8')

    admin = User(school_id=school.id, email='admin@test.edu',
                 password_hash=pw, role='admin', name='Test Admin')
    student = User(school_id=school.id, email='student@test.edu',
                   password_hash=pw, role='student', name='Test Student')
    professor = User(school_id=school.id, email='prof@test.edu',
                     password_hash=pw, role='professor', name='Test Professor')

    db.session.add_all([admin, student, professor])
    db.session.commit()

    db.session.add(Student(user_id=student.id, section_id=section.id, enrollment_year=2025))
    db.session.commit()

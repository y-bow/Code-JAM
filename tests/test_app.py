def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Hive' in response.data or b'hive' in response.data or b'Login' in response.data


def test_index_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_login_with_valid_credentials(client):
    response = client.post('/login', data={
        'email': 'admin@test.edu',
        'password': 'test1234',
    }, follow_redirects=True)
    assert response.status_code == 200


def test_login_with_invalid_credentials(client):
    response = client.post('/login', data={
        'email': 'wrong@test.edu',
        'password': 'wrongpassword',
    }, follow_redirects=True)
    assert b'Invalid' in response.data or b'invalid' in response.data or b'error' in response.data


def test_app_exists(app):
    assert app is not None


def test_database_has_seed_data(app, db_session):
    from app.models import User
    user_count = User.query.count()
    assert user_count > 0

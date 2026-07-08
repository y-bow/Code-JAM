from flask_smorest import Api


api = Api()


def init_api(app):
    api.init_app(app)

    from .auth import blp as auth_blp
    from .timetable import blp as timetable_blp

    api.register_blueprint(auth_blp)
    api.register_blueprint(timetable_blp)

    from flask_wtf.csrf import CSRFProtect
    csrf = app.extensions.get('csrf')
    if csrf:
        csrf.exempt(auth_blp)
        csrf.exempt(timetable_blp)

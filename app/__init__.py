import os
from flask import Flask, redirect, url_for, session
from dotenv import load_dotenv
from .models import db, bcrypt

load_dotenv()

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')
    
    # Configuration
    # Safe absolute pathing for SQLite on Windows (uses 4 slashes)
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'app.db').replace('\\', '/')
    if not db_path.startswith('/'):
        db_path = '/' + db_path
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite://{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)
    
    from flask_migrate import Migrate
    from .cli import hive_cli
    app.cli.add_command(hive_cli)
    migrate = Migrate(app, db)

    from app.models import get_setting as _get_setting

    @app.context_processor
    def inject_settings():
        return dict(get_setting=_get_setting)

    @app.template_filter('fix_time')
    def fix_time_filter(s):
        return s.replace(" ", "") if s else s

    # Session Security
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=1800, # 30 minutes
    )

    from .services.setup_service import is_setup_complete

    @app.before_request
    def check_setup():
        from flask import request, redirect, url_for
        if request.endpoint and 'static' not in request.endpoint and 'setup' not in request.endpoint:
            if not is_setup_complete():
                return redirect(url_for('setup.wizard'))

    @app.after_request
    def add_header(response):
        """
        Prevent browser caching of sensitive pages to avoid 'account swapping'
        when multiple users use the same machine/browser.
        """
        if 'user_id' in session:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    # Register blueprints
    from .core.auth import init_module as init_auth
    init_auth(app)
    from .routes.academics import academics_bp
    from .routes.timetable import timetable_bp
    from .routes.tasks import tasks_bp
    from .routes.analytics import analytics_bp
    from .routes.admin import admin_bp
    from .routes.classroom import classroom_bp
    from .routes.messages import messages_bp
    from .routes.fees import fees_bp
    from .routes.internships import internships_bp
    from .routes.lost_found import lost_found_bp
    from .routes.clubs import clubs_bp
    from .routes.imports import import_bp
    from .routes.setup import setup_bp

    app.register_blueprint(academics_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(classroom_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(fees_bp)
    app.register_blueprint(internships_bp)
    app.register_blueprint(lost_found_bp)
    app.register_blueprint(clubs_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(setup_bp)

    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('role')
            if role in ('student', 'class_rep'):
                return redirect(url_for('academics.student_dashboard'))
            elif role in ('professor', 'assistant_professor'):
                return redirect(url_for('academics.teacher_dashboard'))
            elif role == 'dean':
                return redirect(url_for('analytics.school_analytics'))
            elif role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('auth.login'))

    return app

import os
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from .models import db, bcrypt

load_dotenv()

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')
    
    # Configuration
    # Safe absolute pathing for SQLite on Windows (uses 4 slashes)
    db_path = os.path.join(app.instance_path, 'app.db').replace('\\', '/')
    if not db_path.startswith('/'):
        db_path = '/' + db_path
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite://{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.classroom import classroom_bp
    from .routes.messages import messages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(classroom_bp)
    app.register_blueprint(messages_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app

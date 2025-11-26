"""
Main Flask application entry point
OvenMediaEngine Web UI
"""
from flask import Flask, render_template, jsonify
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
import logging
import os

from config import config
from models import db, User
from services import OMEClient

# Import blueprints
from api.auth import auth_bp
from api.server import server_bp
from api.virtualhosts import virtualhosts_bp
from api.applications import applications_bp
from api.streams import streams_bp
from api.logs import logs_bp

def create_app(config_name=None):
    """Application factory pattern"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    jwt = JWTManager(app)
    CORS(app)
    
    # Configure logging
    setup_logging(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(server_bp, url_prefix='/api/server')
    app.register_blueprint(virtualhosts_bp, url_prefix='/api/virtualhosts')
    app.register_blueprint(applications_bp, url_prefix='/api/applications')
    app.register_blueprint(streams_bp, url_prefix='/api/streams')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    
    # Initialize OME client as app extension
    @app.before_first_request
    def initialize():
        """Initialize on first request"""
        app.ome_client = OMEClient(
            app.config['OME_API_URL'],
            app.config['OME_API_ACCESS_TOKEN']
        )
        app.logger.info("OME Client initialized")
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Main routes
    @app.route('/')
    def index():
        """Main dashboard"""
        return render_template('index.html')
    
    @app.route('/login')
    def login():
        """Login page"""
        return render_template('login.html')
    
    @app.route('/server')
    def server_config():
        """Server configuration page"""
        return render_template('server_config.html')
    
    @app.route('/virtualhosts')
    def virtualhosts():
        """Virtual hosts management page"""
        return render_template('virtualhosts.html')
    
    @app.route('/applications')
    def applications():
        """Applications management page"""
        return render_template('applications.html')
    
    @app.route('/transcoding')
    def transcoding():
        """Transcoding configuration page"""
        return render_template('transcoding.html')
    
    @app.route('/monitoring')
    def monitoring():
        """Monitoring and logs page"""
        return render_template('monitoring.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        if app.config['DEBUG']:
            return jsonify({'error': 'Not found'}), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Internal error: {error}')
        if app.config['DEBUG']:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500
    
    return app


def setup_logging(app):
    """Setup application logging"""
    log_level = getattr(logging, app.config['LOG_LEVEL'])
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    file_handler = logging.FileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(log_level)
    file_handler.setFormatter(console_formatter)
    
    # Add handlers
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)


# CLI commands
def init_db_command(app):
    """Initialize database with default data"""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@localhost',
                role=User.ROLE_ADMIN
            )
            admin.set_password('admin123')  # Change this!
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Default admin user created")


if __name__ == '__main__':
    app = create_app()
    
    # Initialize database on first run
    with app.app_context():
        db.create_all()
        init_db_command(app)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

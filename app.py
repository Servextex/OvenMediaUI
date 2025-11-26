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
from api.settings import settings_bp

def create_app(config_name=None):
    """Application factory pattern"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Store config class for later reinitialization
    app.config.init_app = config[config_name].init_app
    
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
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # Initialize settings in a temporary context
    with app.app_context():
        try:
            # Initialize settings from database  
            config[config_name].init_app(app)
            
            # Initialize OME client with settings from DB
            app.ome_client = OMEClient(
                app.config.get('OME_API_URL', 'http://localhost:8081'),
                app.config.get('OME_API_ACCESS_TOKEN', '')
            )
            app.logger.info("Application initialized with database settings")
        except:
            # If DB not ready, use defaults
            app.ome_client = OMEClient('http://localhost:8081', '')
    
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
    
    @app.route('/settings')
    def app_settings():
        """Application settings page"""
        return render_template('settings.html')
    
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
    """Configure logging for the application"""
    if not app.debug:
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Get log level from config with fallback
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
        
        # File handler
        file_handler = logging.handlers.RotatingFileHandler(
            app.config.get('LOG_FILE', 'logs/app.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        app.logger.info('OvenMediaEngine Web UI startup')



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

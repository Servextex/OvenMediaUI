"""
Configuration module for OvenMediaEngine Web UI
Now reads from database Settings model, with environment variable fallbacks
"""
import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables as fallback
load_dotenv()


class Config:
    """Base configuration - reads from database Settings or environment variables"""
    
    # Database - Only this uses environment variable (needed to connect to DB first)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ome_ui.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        """Initialize app with settings from database"""
        # Import here to avoid circular import
        from models.settings import Settings
        
        # Initialize default settings if needed
        with app.app_context():
            try:
                Settings.initialize_defaults()
                
                # Load settings from database
                secret_key = Settings.get('secret_key')
                if not secret_key:
                    # Generate new secret key if not set
                    secret_key = secrets.token_hex(32)
                    Settings.set('secret_key', secret_key, Settings.CATEGORY_SECURITY, user_id=None)
                app.config['SECRET_KEY'] = secret_key
                
                # JWT Configuration
                jwt_secret = Settings.get('jwt_secret_key')
                if not jwt_secret:
                    jwt_secret = secrets.token_hex(32)
                    Settings.set('jwt_secret_key', jwt_secret, Settings.CATEGORY_SECURITY, user_id=None)
                app.config['JWT_SECRET_KEY'] = jwt_secret
                
                jwt_expires = int(Settings.get('jwt_token_expires', '3600'))
                app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=jwt_expires)
                
                # OvenMediaEngine Configuration
                app.config['OME_SERVER_XML_PATH'] = Settings.get('ome_server_xml_path', '/usr/share/ovenmediaengine/conf/Server.xml')
                app.config['OME_API_URL'] = Settings.get('ome_api_url', 'http://localhost:8081')
                app.config['OME_API_ACCESS_TOKEN'] = Settings.get('ome_api_access_token', '')
                
                # Application Settings
                app.config['ITEMS_PER_PAGE'] = int(Settings.get('items_per_page', '20'))
                app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
                
                # Logging
                app.config['LOG_LEVEL'] = Settings.get('log_level', 'INFO')
                app.config['LOG_FILE'] = 'logs/app.log'
                
            except Exception as e:
                # Fallback to environment variables if database not ready
                app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
                app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or app.config['SECRET_KEY']
                app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
                app.config['OME_SERVER_XML_PATH'] = os.environ.get('OME_SERVER_XML_PATH', '/usr/share/ovenmediaengine/conf/Server.xml')
                app.config['OME_API_URL'] = os.environ.get('OME_API_URL', 'http://localhost:8081')
                app.config['OME_API_ACCESS_TOKEN'] = os.environ.get('OME_API_ACCESS_TOKEN', '')
                app.config['ITEMS_PER_PAGE'] = int(os.environ.get('ITEMS_PER_PAGE', 20))
                app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
                app.config['LOG_LEVEL'] = os.environ.get('LOG_LEVEL', 'INFO')
                app.config['LOG_FILE'] = os.environ.get('LOG_FILE', 'logs/app.log')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

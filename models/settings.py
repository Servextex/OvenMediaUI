"""
Settings model for database-based configuration
All application settings stored in database instead of environment variables
"""
from datetime import datetime
from . import db


class Settings(db.Model):
    """Model to store application settings in database"""
    
    __tablename__ = 'settings'
    
    # Setting categories
    CATEGORY_GENERAL = 'general'
    CATEGORY_OME = 'ome'
    CATEGORY_SECURITY = 'security'
    CATEGORY_DATABASE = 'database'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500))
    is_secret = db.Column(db.Boolean, default=False)  # For sensitive data like tokens
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Setting {self.key}>'
    
    @classmethod
    def get(cls, key, default=None):
        """Get a setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set(cls, key, value, category=CATEGORY_GENERAL, description=None, is_secret=False, user_id=None):
        """Set a setting value"""
        setting = cls.query.filter_by(key=key).first()
        
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
            setting.updated_by = user_id
        else:
            setting = cls(
                key=key,
                value=value,
                category=category,
                description=description,
                is_secret=is_secret,
                updated_by=user_id
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @classmethod
    def get_by_category(cls, category):
        """Get all settings in a category"""
        return cls.query.filter_by(category=category).all()
    
    @classmethod
    def get_all_as_dict(cls):
        """Get all settings as dictionary"""
        settings = cls.query.all()
        return {s.key: s.value for s in settings}
    
    @classmethod
    def initialize_defaults(cls):
        """Initialize default settings if not exist"""
        defaults = [
            # General Settings
            ('app_name', 'OvenMediaEngine Web UI', cls.CATEGORY_GENERAL, 'Application name', False),
            ('items_per_page', '20', cls.CATEGORY_GENERAL, 'Items per page in lists', False),
            ('log_level', 'INFO', cls.CATEGORY_GENERAL, 'Logging level (DEBUG, INFO, WARNING, ERROR)', False),
            
            # OvenMediaEngine Settings
            ('ome_server_xml_path', '/usr/share/ovenmediaengine/conf/Server.xml', cls.CATEGORY_OME, 'Path to OvenMediaEngine Server.xml', False),
            ('ome_api_url', 'http://localhost:8081', cls.CATEGORY_OME, 'OvenMediaEngine REST API URL', False),
            ('ome_api_access_token', '', cls.CATEGORY_OME, 'OvenMediaEngine API access token', True),
            
            # Security Settings
            ('secret_key', '', cls.CATEGORY_SECURITY, 'Flask secret key (auto-generated if empty)', True),
            ('jwt_secret_key', '', cls.CATEGORY_SECURITY, 'JWT secret key (auto-generated if empty)', True),
            ('jwt_token_expires', '3600', cls.CATEGORY_SECURITY, 'JWT token expiration in seconds', False),
            ('session_timeout', '3600', cls.CATEGORY_SECURITY, 'Session timeout in seconds', False),
        ]
        
        for key, value, category, description, is_secret in defaults:
            existing = cls.query.filter_by(key=key).first()
            if not existing:
                setting = cls(
                    key=key,
                    value=value,
                    category=category,
                    description=description,
                    is_secret=is_secret
                )
                db.session.add(setting)
        
        db.session.commit()
    
    def to_dict(self, include_secret=False):
        """Convert setting to dictionary"""
        data = {
            'id': self.id,
            'key': self.key,
            'value': '***HIDDEN***' if self.is_secret and not include_secret else self.value,
            'category': self.category,
            'description': self.description,
            'is_secret': self.is_secret,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return data

"""
Configuration snapshot model for versioning
"""
from datetime import datetime
from . import db


class ConfigurationSnapshot(db.Model):
    """Model to store configuration snapshots with versioning"""
    
    __tablename__ = 'configuration_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False, index=True)
    description = db.Column(db.String(500))
    configuration_type = db.Column(db.String(50), nullable=False, default='server_xml')  # server_xml, vhost, application
    configuration_data = db.Column(db.Text, nullable=False)  # XML or JSON string
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=False)  # Only one active snapshot at a time
    
    def __repr__(self):
        return f'<ConfigurationSnapshot v{self.version}>'
    
    @classmethod
    def get_latest_version(cls):
        """Get the latest version number"""
        latest = cls.query.order_by(cls.version.desc()).first()
        return latest.version if latest else 0
    
    @classmethod
    def get_active(cls):
        """Get the currently active configuration"""
        return cls.query.filter_by(is_active=True).first()
    
    def activate(self):
        """Set this snapshot as active and deactivate others"""
        # Deactivate all other snapshots
        ConfigurationSnapshot.query.filter_by(is_active=True).update({'is_active': False})
        self.is_active = True
        db.session.commit()
    
    def to_dict(self):
        """Convert snapshot to dictionary"""
        return {
            'id': self.id,
            'version': self.version,
            'description': self.description,
            'configuration_type': self.configuration_type,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

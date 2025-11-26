"""
Audit log model for tracking all changes
"""
from datetime import datetime
from . import db


class AuditLog(db.Model):
    """Model to track all user actions for security and compliance"""
    
    __tablename__ = 'audit_logs'
    
    # Action types
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_READ = 'read'
    ACTION_ROLLBACK = 'rollback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False, index=True)
    resource_type = db.Column(db.String(100), nullable=False)  # server, vhost, application, stream
    resource_id = db.Column(db.String(200))  # identifier of the resource
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    status = db.Column(db.String(20), default='success')  # success, failure
    error_message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by user {self.user_id}>'
    
    @classmethod
    def log_action(cls, user_id, action, resource_type, resource_id=None, 
                   description=None, ip_address=None, user_agent=None, 
                   status='success', error_message=None):
        """Helper method to create audit log entries"""
        log = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'ip_address': self.ip_address,
            'status': self.status,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

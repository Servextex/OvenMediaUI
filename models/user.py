"""
User model for authentication and authorization
"""
from datetime import datetime
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from . import db


class User(UserMixin, db.Model):
    """User model with role-based access control"""
    
    __tablename__ = 'users'
    
    # Role constants
    ROLE_ADMIN = 'admin'
    ROLE_OPERATOR = 'operator'
    ROLE_VIEWER = 'viewer'
    
    ROLES = [ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER]
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_VIEWER)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify the user's password"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission based on role"""
        permissions = {
            self.ROLE_ADMIN: ['read', 'write', 'delete', 'manage_users'],
            self.ROLE_OPERATOR: ['read', 'write'],
            self.ROLE_VIEWER: ['read']
        }
        return permission in permissions.get(self.role, [])
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == self.ROLE_ADMIN
    
    def is_operator(self):
        """Check if user is operator or admin"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_OPERATOR]
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

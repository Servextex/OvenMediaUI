"""
Models package for OvenMediaEngine Web UI
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models after db is defined
from .user import User
from .configuration import ConfigurationSnapshot
from .audit import AuditLog

__all__ = ['db', 'User', 'ConfigurationSnapshot', 'AuditLog']

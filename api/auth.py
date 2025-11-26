"""
Authentication API Blueprint
Handles user login, logout, and session management
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity,
    get_jwt
)
from datetime import datetime

from models import db, User, AuditLog

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token
    
    Request JSON:
        {
            "username": "string",
            "password": "string"
        }
    
    Returns:
        {
            "access_token": "string",
            "user": {...}
        }
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    password = data['password']
    
    # Find user
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        # Log failed attempt
        if user:
            AuditLog.log_action(
                user_id=user.id,
                action=AuditLog.ACTION_LOGIN,
                resource_type='auth',
                description='Failed login attempt',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                status='failure',
                error_message='Invalid password'
            )
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Log successful login
    AuditLog.log_action(
        user_id=user.id,
        action=AuditLog.ACTION_LOGIN,
        resource_type='auth',
        description='Successful login',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (client should delete token)
    """
    user_id = get_jwt_identity()
    
    # Log logout
    AuditLog.log_action(
        user_id=user_id,
        action=AuditLog.ACTION_LOGOUT,
        resource_type='auth',
        description='User logged out',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user information
    
    Returns:
        User object as JSON
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """
    List all users (admin only)
    """
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user or not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@auth_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """
    Create new user (admin only)
    
    Request JSON:
        {
            "username": "string",
            "email": "string",
            "password": "string",
            "role": "admin|operator|viewer"
        }
    """
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user or not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required = ['username', 'email', 'password', 'role']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Validate role
    if data['role'] not in User.ROLES:
        return jsonify({'error': f"Invalid role. Must be one of: {', '.join(User.ROLES)}"}), 400
    
    # Create user
    new_user = User(
        username=data['username'],
        email=data['email'],
        role=data['role']
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action=AuditLog.ACTION_CREATE,
        resource_type='user',
        resource_id=str(new_user.id),
        description=f'Created user: {new_user.username}',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    return jsonify(new_user.to_dict()), 201

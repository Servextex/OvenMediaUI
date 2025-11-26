"""
Applications API Blueprint
Manages applications within virtual hosts
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User, AuditLog
from services.ome_client import OMEAPIException

applications_bp = Blueprint('applications', __name__)


@applications_bp.route('/<vhost_name>/apps', methods=['GET'])
@jwt_required()
def list_apps(vhost_name):
    """List all applications in a virtual host"""
    try:
        apps = current_app.ome_client.list_apps(vhost_name)
        return jsonify(apps), 200
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 500


@applications_bp.route('/<vhost_name>/apps/<app_name>', methods=['GET'])
@jwt_required()
def get_app(vhost_name, app_name):
    """Get details of a specific application"""
    try:
        app = current_app.ome_client.get_app(vhost_name, app_name)
        return jsonify(app), 200
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 404


@applications_bp.route('/<vhost_name>/apps', methods=['POST'])
@jwt_required()
def create_app(vhost_name):
    """Create a new application"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('write'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        result = current_app.ome_client.create_app(vhost_name, data)
        
        # Log action
        AuditLog.log_action(
            user_id=user.id,
            action=AuditLog.ACTION_CREATE,
            resource_type='application',
            resource_id=f"{vhost_name}/{data.get('name')}",
            description=f"Created application: {data.get('name')} in {vhost_name}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify(result), 201
        
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 400


@applications_bp.route('/<vhost_name>/apps/<app_name>', methods=['PUT'])
@jwt_required()
def update_app(vhost_name, app_name):
    """Update an existing application"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('write'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        result = current_app.ome_client.update_app(vhost_name, app_name, data)
        
        # Log action
        AuditLog.log_action(
            user_id=user.id,
            action=AuditLog.ACTION_UPDATE,
            resource_type='application',
            resource_id=f"{vhost_name}/{app_name}",
            description=f"Updated application: {app_name} in {vhost_name}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify(result), 200
        
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 400


@applications_bp.route('/<vhost_name>/apps/<app_name>', methods=['DELETE'])
@jwt_required()
def delete_app(vhost_name, app_name):
    """Delete an application"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('delete'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        success = current_app.ome_client.delete_app(vhost_name, app_name)
        
        if success:
            # Log action
            AuditLog.log_action(
                user_id=user.id,
                action=AuditLog.ACTION_DELETE,
                resource_type='application',
                resource_id=f"{vhost_name}/{app_name}",
                description=f"Deleted application: {app_name} from {vhost_name}",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify({'message': 'Application deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete application'}), 500
            
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 400

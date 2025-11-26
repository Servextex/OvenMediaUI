"""
VirtualHosts API Blueprint
Manages OvenMediaEngine Virtual Hosts
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User, AuditLog
from services.ome_client import OMEAPIException

virtualhosts_bp = Blueprint('virtualhosts', __name__)


@virtualhosts_bp.route('/', methods=['GET'])
@jwt_required()
def list_vhosts():
    """List all virtual hosts"""
    try:
        vhosts = current_app.ome_client.list_vhosts()
        return jsonify(vhosts), 200
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 500


@virtualhosts_bp.route('/<vhost_name>', methods=['GET'])
@jwt_required()
def get_vhost(vhost_name):
    """Get details of a specific virtual host"""
    try:
        vhost = current_app.ome_client.get_vhost(vhost_name)
        return jsonify(vhost), 200
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 404


@virtualhosts_bp.route('/', methods=['POST'])
@jwt_required()
def create_vhost():
    """
    Create a new virtual host
    
    Request JSON:
        {
            "name": "string",
            "host": {...}
        }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('write'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        result = current_app.ome_client.create_vhost(data)
        
        # Log action
        AuditLog.log_action(
            user_id=user.id,
            action=AuditLog.ACTION_CREATE,
            resource_type='virtualhost',
            resource_id=data.get('name'),
            description=f"Created virtual host: {data.get('name')}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify(result), 201
        
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 400


@virtualhosts_bp.route('/<vhost_name>', methods=['PUT'])
@jwt_required()
def update_vhost(vhost_name):
    """Update an existing virtual host"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('write'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        result = current_app.ome_client.update_vhost(vhost_name, data)
        
        # Log action
        AuditLog.log_action(
            user_id=user.id,
            action=AuditLog.ACTION_UPDATE,
            resource_type='virtualhost',
            resource_id=vhost_name,
            description=f"Updated virtual host: {vhost_name}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify(result), 200
        
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 400


@virtualhosts_bp.route('/<vhost_name>', methods=['DELETE'])
@jwt_required()
def delete_vhost(vhost_name):
    """Delete a virtual host"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('delete'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        success = current_app.ome_client.delete_vhost(vhost_name)
        
        if success:
            # Log action
            AuditLog.log_action(
                user_id=user.id,
                action=AuditLog.ACTION_DELETE,
                resource_type='virtualhost',
                resource_id=vhost_name,
                description=f"Deleted virtual host: {vhost_name}",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify({'message': 'Virtual host deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete virtual host'}), 500
            
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 400

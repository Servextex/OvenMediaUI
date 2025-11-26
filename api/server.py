"""
Server Configuration API Blueprint
Manages Server.xml configuration
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, User, ConfigurationSnapshot, AuditLog
from services import ConfigManager, XMLParser

server_bp = Blueprint('server', __name__)


def get_config_manager():
    """Get ConfigManager instance with current app config"""
    return ConfigManager(
        xml_path=current_app.config['OME_SERVER_XML_PATH'],
        ome_client=current_app.ome_client
    )


@server_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    """
    Get current server configuration
    
    Returns:
        Complete Server.xml content
    """
    try:
        config_manager = get_config_manager()
        # We need raw XML for the editor
        with open(config_manager.xml_path, 'r') as f:
            raw_xml = f.read()
            
        server_info = config_manager.get_server_info()
        
        return jsonify({
            'config': raw_xml,
            'server_info': server_info
        }), 200
        
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error reading config: {str(e)}")
        return jsonify({'error': 'Failed to read configuration'}), 500


@server_bp.route('/config', methods=['PUT'])
@jwt_required()
def update_config():
    """
    Update server configuration
    
    Request JSON:
        {
            "config": "xml string",
            "description": "string" (optional)
        }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permissions
    if not user or not user.has_permission('write'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'config' not in data:
        return jsonify({'error': 'Configuration data required'}), 400
    
    try:
        config_manager = get_config_manager()
        new_config_xml = data['config']
        
        # Validate XML structure
        is_valid, error = XMLParser.validate_xml(new_config_xml)
        if not is_valid:
            return jsonify({'error': f'Invalid XML: {error}'}), 400
        
        # Create snapshot before updating
        with open(config_manager.xml_path, 'r') as f:
            old_config_xml = f.read()
            
        version = ConfigurationSnapshot.get_latest_version() + 1
        
        snapshot = ConfigurationSnapshot(
            version=version,
            description=data.get('description', 'Configuration update'),
            configuration_type='server_xml',
            configuration_data=old_config_xml,
            user_id=user.id
        )
        db.session.add(snapshot)
        
        # Write new configuration directly as file
        with open(config_manager.xml_path, 'w') as f:
            f.write(new_config_xml)
        
        # Commit snapshot
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=user.id,
            action=AuditLog.ACTION_UPDATE,
            resource_type='server_config',
            description=data.get('description', 'Updated server configuration'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Configuration updated successfully',
            'snapshot_version': version
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating config: {str(e)}")
        return jsonify({'error': str(e)}), 500


@server_bp.route('/status', methods=['GET'])
@jwt_required()
def get_status():
    """
    Get OvenMediaEngine server status
    """
    try:
        config_manager = get_config_manager()
        is_connected, error = config_manager.test_ome_connection()
        
        result = {
            'api_connected': is_connected,
            'api_url': current_app.config['OME_API_URL']
        }
        
        if error:
            result['error'] = error
        
        # Try to get server stats
        if is_connected:
            try:
                stats = current_app.ome_client.get_server_stats()
                result['stats'] = stats
            except:
                pass
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@server_bp.route('/snapshots', methods=['GET'])
@jwt_required()
def list_snapshots():
    """Get list of configuration snapshots"""
    snapshots = ConfigurationSnapshot.query.order_by(
        ConfigurationSnapshot.created_at.desc()
    ).limit(50).all()
    
    return jsonify([s.to_dict() for s in snapshots]), 200


@server_bp.route('/snapshots/<int:snapshot_id>/restore', methods=['POST'])
@jwt_required()
def restore_snapshot(snapshot_id):
    """
    Restore configuration from snapshot
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('write'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    snapshot = ConfigurationSnapshot.query.get(snapshot_id)
    if not snapshot:
        return jsonify({'error': 'Snapshot not found'}), 404
    
    try:
        config_manager = get_config_manager()
        
        # Restore from snapshot
        config_manager.restore_from_snapshot(snapshot.configuration_data)
        
        # Activate this snapshot
        snapshot.activate()
        
        # Log action
        AuditLog.log_action(
            user_id=user.id,
            action=AuditLog.ACTION_ROLLBACK,
            resource_type='server_config',
            resource_id=str(snapshot_id),
            description=f'Restored configuration to version {snapshot.version}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Configuration restored successfully',
            'version': snapshot.version
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error restoring snapshot: {str(e)}")
        return jsonify({'error': str(e)}), 500

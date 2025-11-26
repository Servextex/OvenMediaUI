"""
Settings API Blueprint
Manages application settings stored in database
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, User, Settings, AuditLog

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_settings():
    """
    Get all settings grouped by category
    Secrets are hidden unless user is admin
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only admins can view all settings
    if not user.is_operator():
        return jsonify({'error': 'Unauthorized'}), 403
    
    is_admin = user.is_admin()
    
    # Get all settings grouped by category
    categories = {}
    for setting in Settings.query.all():
        if setting.category not in categories:
            categories[setting.category] = []
        categories[setting.category].append(setting.to_dict(include_secret=is_admin))
    
    return jsonify(categories), 200


@settings_bp.route('/<key>', methods=['GET'])
@jwt_required()
def get_setting(key):
    """Get a specific setting"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_operator():
        return jsonify({'error': 'Unauthorized'}), 403
    
    setting = Settings.query.filter_by(key=key).first()
    if not setting:
        return jsonify({'error': 'Setting not found'}), 404
    
    return jsonify(setting.to_dict(include_secret=user.is_admin())), 200


@settings_bp.route('/', methods=['PUT'])
@jwt_required()
def update_settings():
    """
    Update multiple settings at once
    
    Request JSON:
        {
            "settings": [
                {"key": "ome_api_url", "value": "http://localhost:8081"},
                {"key": "items_per_page", "value": "25"}
            ]
        }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admins can update settings
    if not user or not user.is_admin():
        return jsonify({'error': 'Unauthorized - Admin access required'}), 403
    
    data = request.get_json()
    if not data or 'settings' not in data:
        return jsonify({'error': 'Settings data required'}), 400
    
    updated = []
    errors = []
    
    for item in data['settings']:
        if 'key' not in item or 'value' not in item:
            errors.append({'error': 'Missing key or value', 'item': item})
            continue
        
        try:
            setting = Settings.query.filter_by(key=item['key']).first()
            if setting:
                old_value = setting.value
                setting.value = item['value']
                setting.updated_by = user.id
                db.session.commit()
                
                updated.append(item['key'])
                
                # Log the change
                AuditLog.log_action(
                    user_id=user.id,
                    action=AuditLog.ACTION_UPDATE,
                    resource_type='setting',
                    resource_id=item['key'],
                    description=f"Updated setting {item['key']} from '{old_value}' to '{item['value']}'",
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
            else:
                errors.append({'error': 'Setting not found', 'key': item['key']})
        except Exception as e:
            errors.append({'error': str(e), 'key': item['key']})
            db.session.rollback()
    
    # Reload configuration in current app
    try:
        current_app.config.init_app(current_app)
    except:
        pass
    
    return jsonify({
        'message': f'Updated {len(updated)} settings',
        'updated': updated,
        'errors': errors
    }), 200


@settings_bp.route('/reload', methods=['POST'])
@jwt_required()
def reload_settings():
    """
    Reload settings from database into application config
    Useful after updating settings
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        current_app.config.init_app(current_app)
        
        # Also update OME client with new settings
        from services import OMEClient
        current_app.ome_client = OMEClient(
            current_app.config['OME_API_URL'],
            current_app.config['OME_API_ACCESS_TOKEN']
        )
        
        # Log action
        AuditLog.log_action(
            user_id=user.id,
            action=AuditLog.ACTION_UPDATE,
            resource_type='settings',
            description='Reloaded application settings',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'Settings reloaded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

"""
Logs API Blueprint
Access to audit logs and OvenMediaEngine logs
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User, AuditLog

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/audit', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """
    Get audit logs
    
    Query parameters:
        - limit: int (default 50, max 200)
        - offset: int (default 0)
        - action: filter by action type
        - user_id: filter by user
        - resource_type: filter by resource type
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admins and operators can view audit logs
    if not user or not user.is_operator():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get query parameters
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    action = request.args.get('action')
    filter_user_id = request.args.get('user_id')
    resource_type = request.args.get('resource_type')
    
    # Build query
    query = AuditLog.query
    
    if action:
        query = query.filter_by(action=action)
    if filter_user_id:
        query = query.filter_by(user_id=int(filter_user_id))
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    # Get total count
    total = query.count()
    
    # Get logs
    logs = query.order_by(AuditLog.timestamp.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
    
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'logs': [log.to_dict() for log in logs]
    }), 200

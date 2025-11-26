"""
Streams API Blueprint
Manages and monitors streams
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User
from services.ome_client import OMEAPIException

streams_bp = Blueprint('streams', __name__)


@streams_bp.route('/<vhost_name>/<app_name>', methods=['GET'])
@jwt_required()
def list_streams(vhost_name, app_name):
    """List all streams in an application"""
    try:
        streams = current_app.ome_client.list_streams(vhost_name, app_name)
        return jsonify(streams), 200
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 500


@streams_bp.route('/<vhost_name>/<app_name>/<stream_name>', methods=['GET'])
@jwt_required()
def get_stream(vhost_name, app_name, stream_name):
    """Get details of a specific stream"""
    try:
        stream = current_app.ome_client.get_stream(vhost_name, app_name, stream_name)
        return jsonify(stream), 200
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 404


@streams_bp.route('/<vhost_name>/<app_name>/<stream_name>/stats', methods=['GET'])
@jwt_required()
def get_stream_stats(vhost_name, app_name, stream_name):
    """Get statistics for a specific stream"""
    try:
        stats = current_app.ome_client.get_stream_stats(vhost_name, app_name, stream_name)
        return jsonify(stats), 200
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 500


@streams_bp.route('/<vhost_name>/<app_name>/<stream_name>', methods=['DELETE'])
@jwt_required()
def delete_stream(vhost_name, app_name, stream_name):
    """Delete/stop a stream"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('write'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        success = current_app.ome_client.delete_stream(vhost_name, app_name, stream_name)
        
        if success:
            return jsonify({'message': 'Stream deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete stream'}), 500
            
    except OMEAPIException as e:
        return jsonify({'error': str(e)}), 400

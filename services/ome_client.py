"""
OvenMediaEngine REST API Client
Handles all communication with OvenMediaEngine's REST API
"""
import requests
from typing import Dict, List, Any, Optional
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger(__name__)


class OMEAPIException(Exception):
    """Exception raised for OME API errors"""
    pass


class OMEClient:
    """Client for OvenMediaEngine REST API"""
    
    def __init__(self, api_url: str, access_token: str, timeout: int = 30):
        """
        Initialize OME API client
        
        Args:
            api_url: Base URL of OME API (e.g., http://localhost:8081)
            access_token: Access token for authentication
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.access_token = access_token
        self.timeout = timeout
        self.session = requests.Session()
        
        # Setup authentication
        if ':' in access_token:
            # Format: user:password
            user, password = access_token.split(':', 1)
            self.session.auth = HTTPBasicAuth(user, password)
        else:
            # Use as Bearer token
            self.session.headers.update({'Authorization': f'Basic {access_token}'})
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to OME API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            OMEAPIException: If request fails
        """
        url = f"{self.api_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"OME API error: {error_msg}")
            raise OMEAPIException(error_msg)
        except requests.exceptions.RequestException as e:
            logger.error(f"OME API connection error: {str(e)}")
            raise OMEAPIException(f"Connection error: {str(e)}")
    
    # VirtualHost Management
    
    def list_vhosts(self) -> List[Dict[str, Any]]:
        """Get list of all virtual hosts"""
        response = self._request('GET', '/v1/vhosts')
        return response.json().get('response', [])
    
    def get_vhost(self, vhost_name: str) -> Dict[str, Any]:
        """Get details of a specific virtual host"""
        response = self._request('GET', f'/v1/vhosts/{vhost_name}')
        return response.json().get('response', {})
    
    def create_vhost(self, vhost_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new virtual host"""
        response = self._request('POST', '/v1/vhosts', json=vhost_config)
        return response.json().get('response', {})
    
    def update_vhost(self, vhost_name: str, vhost_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing virtual host"""
        response = self._request('PUT', f'/v1/vhosts/{vhost_name}', json=vhost_config)
        return response.json().get('response', {})
    
    def delete_vhost(self, vhost_name: str) -> bool:
        """Delete a virtual host"""
        response = self._request('DELETE', f'/v1/vhosts/{vhost_name}')
        return response.status_code == 200
    
    # Application Management
    
    def list_apps(self, vhost_name: str) -> List[Dict[str, Any]]:
        """Get list of all applications in a virtual host"""
        response = self._request('GET', f'/v1/vhosts/{vhost_name}/apps')
        return response.json().get('response', [])
    
    def get_app(self, vhost_name: str, app_name: str) -> Dict[str, Any]:
        """Get details of a specific application"""
        response = self._request('GET', f'/v1/vhosts/{vhost_name}/apps/{app_name}')
        return response.json().get('response', {})
    
    def create_app(self, vhost_name: str, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new application"""
        response = self._request('POST', f'/v1/vhosts/{vhost_name}/apps', json=app_config)
        return response.json().get('response', {})
    
    def update_app(self, vhost_name: str, app_name: str, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing application"""
        response = self._request('PUT', f'/v1/vhosts/{vhost_name}/apps/{app_name}', json=app_config)
        return response.json().get('response', {})
    
    def delete_app(self, vhost_name: str, app_name: str) -> bool:
        """Delete an application"""
        response = self._request('DELETE', f'/v1/vhosts/{vhost_name}/apps/{app_name}')
        return response.status_code == 200
    
    # Stream Management
    
    def list_streams(self, vhost_name: str, app_name: str) -> List[Dict[str, Any]]:
        """Get list of all streams in an application"""
        response = self._request('GET', f'/v1/vhosts/{vhost_name}/apps/{app_name}/streams')
        return response.json().get('response', [])
    
    def get_stream(self, vhost_name: str, app_name: str, stream_name: str) -> Dict[str, Any]:
        """Get details of a specific stream"""
        response = self._request('GET', f'/v1/vhosts/{vhost_name}/apps/{app_name}/streams/{stream_name}')
        return response.json().get('response', {})
    
    def create_stream(self, vhost_name: str, app_name: str, stream_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new stream (push publishing)"""
        response = self._request('POST', f'/v1/vhosts/{vhost_name}/apps/{app_name}/streams', json=stream_config)
        return response.json().get('response', {})
    
    def delete_stream(self, vhost_name: str, app_name: str, stream_name: str) -> bool:
        """Delete a stream"""
        response = self._request('DELETE', f'/v1/vhosts/{vhost_name}/apps/{app_name}/streams/{stream_name}')
        return response.status_code == 200
    
    # Statistics
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        try:
            response = self._request('GET', '/v1/stats/current')
            return response.json().get('response', {})
        except OMEAPIException:
            # Stats endpoint might not be available in all versions
            return {}
    
    def get_stream_stats(self, vhost_name: str, app_name: str, stream_name: str) -> Dict[str, Any]:
        """Get statistics for a specific stream"""
        try:
            response = self._request('GET', f'/v1/stats/current/vhosts/{vhost_name}/apps/{app_name}/streams/{stream_name}')
            return response.json().get('response', {})
        except OMEAPIException:
            return {}
    
    # Health Check
    
    def health_check(self) -> bool:
        """Check if OME API is accessible"""
        try:
            self._request('GET', '/v1/vhosts')
            return True
        except OMEAPIException:
            return False

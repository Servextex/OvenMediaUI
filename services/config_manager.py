"""
Configuration Manager
Centralized service for managing OvenMediaEngine configurations
"""
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
from .xml_parser import XMLParser
from .ome_client import OMEClient
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages OvenMediaEngine configuration with versioning and rollback"""
    
    def __init__(self, xml_path: str, ome_client: Optional[OMEClient] = None):
        """
        Initialize Configuration Manager
        
        Args:
            xml_path: Path to Server.xml file
            ome_client: Optional OME API client for dynamic operations
        """
        self.xml_path = xml_path
        self.ome_client = ome_client
        self.parser = XMLParser()
    
    def read_config(self) -> Dict[str, Any]:
        """
        Read current configuration from Server.xml
        
        Returns:
            Configuration as dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        return self.parser.parse_file(self.xml_path)
    
    def write_config(self, config: Dict[str, Any], backup: bool = True) -> bool:
        """
        Write configuration to Server.xml
        
        Args:
            config: Configuration dictionary
            backup: Whether to create backup before writing
            
        Returns:
            True if successful
        """
        try:
            # Create backup if requested
            if backup and os.path.exists(self.xml_path):
                backup_path = f"{self.xml_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.xml_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Write new configuration
            self.parser.write_file(config, self.xml_path, pretty=True)
            logger.info(f"Configuration written to {self.xml_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing configuration: {str(e)}")
            raise
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate configuration before applying
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Convert to XML and validate syntax
            xml_string = self.parser.dict_to_xml(config)
            is_valid, error = self.parser.validate_xml(xml_string)
            
            if not is_valid:
                return False, f"XML validation error: {error}"
            
            # Check required fields
            if 'Server' not in config:
                return False, "Missing required 'Server' root element"
            
            server = config['Server']
            
            # Validate version
            if '@version' not in server:
                return False, "Missing server version attribute"
            
            # Check for Bind section
            if 'Bind' not in server:
                return False, "Missing 'Bind' section in configuration"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get basic server information from config"""
        config = self.read_config()
        return self.parser.extract_server_info(config)
    
    def get_virtual_hosts(self) -> list:
        """Get list of virtual hosts from config"""
        config = self.read_config()
        vhosts = config.get('Server', {}).get('VirtualHosts', {}).get('VirtualHost', [])
        
        # Ensure it's a list (xmltodict returns dict for single item)
        if isinstance(vhosts, dict):
            vhosts = [vhosts]
        
        return vhosts
    
    def update_virtual_host(self, vhost_name: str, vhost_config: Dict[str, Any]) -> bool:
        """
        Update a virtual host in the configuration
        
        Args:
            vhost_name: Name of the virtual host
            vhost_config: New configuration for the virtual host
            
        Returns:
            True if successful
        """
        config = self.read_config()
        vhosts = config.get('Server', {}).get('VirtualHosts', {}).get('VirtualHost', [])
        
        if isinstance(vhosts, dict):
            vhosts = [vhosts]
        
        # Find and update the vhost
        updated = False
        for i, vhost in enumerate(vhosts):
            if vhost.get('Name') == vhost_name:
                vhosts[i] = vhost_config
                updated = True
                break
        
        if updated:
            # Update the config
            if isinstance(config['Server']['VirtualHosts']['VirtualHost'], list):
                config['Server']['VirtualHosts']['VirtualHost'] = vhosts
            else:
                config['Server']['VirtualHosts']['VirtualHost'] = vhosts[0]
            
            return self.write_config(config)
        
        return False
    
    def create_snapshot(self, description: str = None) -> str:
        """
        Create a snapshot of current configuration
        
        Args:
            description: Optional description for the snapshot
            
        Returns:
            XML string of current configuration
        """
        config = self.read_config()
        xml_string = self.parser.dict_to_xml(config)
        
        logger.info(f"Created configuration snapshot: {description or 'No description'}")
        return xml_string
    
    def restore_from_snapshot(self, xml_string: str) -> bool:
        """
        Restore configuration from snapshot
        
        Args:
            xml_string: XML configuration string
            
        Returns:
            True if successful
        """
        try:
            # Parse and validate
            config = self.parser.parse_string(xml_string)
            is_valid, error = self.validate_config(config)
            
            if not is_valid:
                raise ValueError(f"Invalid configuration: {error}")
            
            # Write configuration
            return self.write_config(config, backup=True)
            
        except Exception as e:
            logger.error(f"Error restoring snapshot: {str(e)}")
            raise
    
    def test_ome_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test connection to OvenMediaEngine API
        
        Returns:
            Tuple of (is_connected, error_message)
        """
        if not self.ome_client:
            return False, "OME client not configured"
        
        try:
            if self.ome_client.health_check():
                return True, None
            else:
                return False, "OME API is not responding"
        except Exception as e:
            return False, str(e)

"""
XML Parser for OvenMediaEngine Server.xml configuration
Provides bidirectional conversion between XML and Python dictionaries
"""
import xmltodict
from lxml import etree
from typing import Dict, Any, Optional


class XMLParser:
    """Parser for OvenMediaEngine XML configurations"""
    
    @staticmethod
    def parse_file(file_path: str) -> Dict[str, Any]:
        """
        Parse XML file to Python dictionary
        
        Args:
            file_path: Path to the XML file
            
        Returns:
            Dictionary representation of XML
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If XML is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            return XMLParser.parse_string(xml_content)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error parsing XML file: {str(e)}")
    
    @staticmethod
    def parse_string(xml_string: str) -> Dict[str, Any]:
        """
        Parse XML string to Python dictionary
        
        Args:
            xml_string: XML content as string
            
        Returns:
            Dictionary representation of XML
            
        Raises:
            ValueError: If XML is invalid
        """
        try:
            return xmltodict.parse(xml_string, process_namespaces=False)
        except Exception as e:
            raise ValueError(f"Error parsing XML string: {str(e)}")
    
    @staticmethod
    def dict_to_xml(data: Dict[str, Any], pretty: bool = True) -> str:
        """
        Convert Python dictionary to XML string
        
        Args:
            data: Dictionary to convert
            pretty: Whether to format with indentation
            
        Returns:
            XML string
        """
        try:
            xml_string = xmltodict.unparse(data, pretty=pretty, indent='  ')
            return xml_string
        except Exception as e:
            raise ValueError(f"Error converting dict to XML: {str(e)}")
    
    @staticmethod
    def write_file(data: Dict[str, Any], file_path: str, pretty: bool = True):
        """
        Write dictionary as XML to file
        
        Args:
            data: Dictionary to write
            file_path: Destination file path
            pretty: Whether to format with indentation
        """
        try:
            xml_string = XMLParser.dict_to_xml(data, pretty=pretty)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_string)
        except Exception as e:
            raise IOError(f"Error writing XML file: {str(e)}")
    
    @staticmethod
    def validate_xml(xml_string: str) -> tuple[bool, Optional[str]]:
        """
        Validate XML syntax
        
        Args:
            xml_string: XML content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            etree.fromstring(xml_string.encode('utf-8'))
            return True, None
        except etree.XMLSyntaxError as e:
            return False, str(e)
    
    @staticmethod
    def get_nested_value(data: Dict[str, Any], path: str, default=None) -> Any:
        """
        Get value from nested dictionary using dot notation
        
        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., 'Server.Bind.Providers.RTMP.Port')
            default: Default value if path not found
            
        Returns:
            Value at path or default
        """
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    @staticmethod
    def set_nested_value(data: Dict[str, Any], path: str, value: Any):
        """
        Set value in nested dictionary using dot notation
        
        Args:
            data: Dictionary to modify
            path: Dot-separated path
            value: Value to set
        """
        keys = path.split('.')
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    @staticmethod
    def extract_server_info(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key server information from configuration
        
        Args:
            config: Parsed Server.xml configuration
            
        Returns:
            Dictionary with server metadata
        """
        server = config.get('Server', {})
        
        return {
            'version': server.get('@version', 'unknown'),
            'name': server.get('Name', 'OvenMediaEngine'),
            'ip': XMLParser.get_nested_value(server, 'IP', '*'),
            'stun_server': XMLParser.get_nested_value(server, 'StunServer'),
            'bind': server.get('Bind', {}),
            'virtual_hosts_count': len(server.get('VirtualHosts', {}).get('VirtualHost', []))
        }

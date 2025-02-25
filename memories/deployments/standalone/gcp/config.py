"""GCP standalone deployment configuration."""

from typing import Dict, Any
import re

class ConfigurationValidator:
    """Validates GCP standalone deployment configuration."""
    
    def validate_cpu_model(self, config: Dict[str, Any]) -> bool:
        """Validate CPU model configuration.
        
        Args:
            config: CPU model configuration
            
        Returns:
            bool: True if valid
        """
        if not isinstance(config, dict):
            return False
            
        required_fields = {'model', 'expected'}
        if not all(field in config for field in required_fields):
            return False
            
        expected = config['expected']
        if not isinstance(expected, dict):
            return False
            
        required_expected = {'base_frequency', 'cores', 'threads'}
        if not all(field in expected for field in required_expected):
            return False
            
        # Validate frequency format
        if not re.match(r'^\d+(\.\d+)?GHz$', expected['base_frequency']):
            return False
            
        # Validate cores and threads
        if not isinstance(expected['cores'], int) or expected['cores'] <= 0:
            return False
            
        if not isinstance(expected['threads'], int) or expected['threads'] <= 0:
            return False
            
        if expected['threads'] < expected['cores']:
            return False
            
        return True
    
    def validate_gpu_specs(self, config: Dict[str, Any]) -> bool:
        """Validate GPU specifications.
        
        Args:
            config: GPU specifications
            
        Returns:
            bool: True if valid
        """
        if not isinstance(config, dict):
            return False
            
        required_fields = {'model', 'expected'}
        if not all(field in config for field in required_fields):
            return False
            
        expected = config['expected']
        if not isinstance(expected, dict):
            return False
            
        required_expected = {'cuda_cores', 'tensor_cores', 'memory'}
        if not all(field in expected for field in required_expected):
            return False
            
        # Validate CUDA cores
        if not isinstance(expected['cuda_cores'], int) or expected['cuda_cores'] <= 0:
            return False
            
        # Validate tensor cores
        if not isinstance(expected['tensor_cores'], int) or expected['tensor_cores'] <= 0:
            return False
            
        # Validate memory format
        if not re.match(r'^\d+GB$', expected['memory']):
            return False
            
        return True
    
    def validate_memory_settings(self, config: Dict[str, Any]) -> bool:
        """Validate memory settings.
        
        Args:
            config: Memory settings
            
        Returns:
            bool: True if valid
        """
        if not isinstance(config, dict):
            return False
            
        required_fields = {'type', 'expected'}
        if not all(field in config for field in required_fields):
            return False
            
        expected = config['expected']
        if not isinstance(expected, dict):
            return False
            
        required_expected = {'channels', 'speed', 'ecc'}
        if not all(field in expected for field in required_expected):
            return False
            
        # Validate channels
        if not isinstance(expected['channels'], int) or expected['channels'] <= 0:
            return False
            
        # Validate speed format
        if not re.match(r'^\d+MHz$', expected['speed']):
            return False
            
        # Validate ECC
        if not isinstance(expected['ecc'], bool):
            return False
            
        return True
    
    def validate_network_settings(self, config: Dict[str, Any]) -> bool:
        """Validate network settings.
        
        Args:
            config: Network settings
            
        Returns:
            bool: True if valid
        """
        if not isinstance(config, dict):
            return False
            
        required_fields = {'expected'}
        if not all(field in config for field in required_fields):
            return False
            
        expected = config['expected']
        if not isinstance(expected, dict):
            return False
            
        required_expected = {'network', 'subnet', 'ip_range'}
        if not all(field in expected for field in required_expected):
            return False
            
        # Validate network name
        if not isinstance(expected['network'], str) or not expected['network']:
            return False
            
        # Validate subnet name
        if not isinstance(expected['subnet'], str) or not expected['subnet']:
            return False
            
        # Validate IP range format (CIDR notation)
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', expected['ip_range']):
            return False
            
        return True 
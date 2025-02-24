import pytest
import yaml
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

# Test configuration path
TEST_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_test.yaml")
DEPLOYMENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "..", "deployments")

@pytest.fixture
def config_validator():
    with open(TEST_CONFIG_PATH, 'r') as f:
        test_config = yaml.safe_load(f)
    return ConfigurationValidator(DEPLOYMENTS_PATH, test_config)

class ConfigurationValidator:
    def __init__(self, config_dir: str, test_config: Dict[str, Any]):
        self.config_dir = config_dir
        self.test_config = test_config
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("ConfigValidator")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def load_config(self, config_file: str) -> Dict[str, Any]:
        full_path = os.path.join(self.config_dir, "standalone", "gcp", config_file)
        with open(full_path, 'r') as f:
            return yaml.safe_load(f)

    def validate_cpu_model(self, params: Dict[str, Any]) -> bool:
        try:
            if params['model'].startswith('ice_lake'):
                config = self.load_config('hardware/cpu/intel.yaml')
            else:
                config = self.load_config('hardware/cpu/amd.yaml')
            
            cpu_model = config['cpu']['models'][params['model']]
            expected = params['expected']
            
            assert cpu_model['cores'] == expected['cores'], f"Core count mismatch"
            assert cpu_model['threads'] == expected['threads'], f"Thread count mismatch"
            assert cpu_model['base_frequency'] == expected['base_frequency'], f"Base frequency mismatch"
            
            self.logger.info(f"CPU model {params['model']} validation passed")
            return True
        except Exception as e:
            self.logger.error(f"CPU model validation failed: {str(e)}")
            return False

    def validate_gpu_specs(self, params: Dict[str, Any]) -> bool:
        try:
            config = self.load_config('hardware/gpu/nvidia.yaml')
            gpu_model = config['gpu']['models'][params['model']]
            expected = params['expected']
            
            assert gpu_model['memory']['size'] == expected['memory'], f"Memory size mismatch"
            assert gpu_model['cuda_cores'] == expected['cuda_cores'], f"CUDA core count mismatch"
            assert gpu_model['tensor_cores'] == expected['tensor_cores'], f"Tensor core count mismatch"
            
            self.logger.info(f"GPU model {params['model']} validation passed")
            return True
        except Exception as e:
            self.logger.error(f"GPU validation failed: {str(e)}")
            return False

    def validate_memory_settings(self, params: Dict[str, Any]) -> bool:
        try:
            config = self.load_config('hardware/memory/config.yaml')
            memory_type = config['memory']['types'][params['type']]
            expected = params['expected']
            
            assert memory_type['speed'] == expected['speed'], f"Memory speed mismatch"
            assert memory_type['channels'] == expected['channels'], f"Channel count mismatch"
            assert memory_type['ecc'] == expected['ecc'], f"ECC setting mismatch"
            
            self.logger.info(f"Memory configuration validation passed")
            return True
        except Exception as e:
            self.logger.error(f"Memory validation failed: {str(e)}")
            return False

    def validate_network_settings(self, params: Dict[str, Any]) -> bool:
        try:
            config = self.load_config('hardware/network/config.yaml')
            network_config = config['network']
            expected = params['expected']
            
            assert network_config['vpc']['network'] == expected['network'], f"VPC network mismatch"
            assert network_config['vpc']['subnet'] == expected['subnet'], f"Subnet mismatch"
            assert network_config['vpc']['ip_range'] == expected['ip_range'], f"IP range mismatch"
            
            self.logger.info("Network configuration validation passed")
            return True
        except Exception as e:
            self.logger.error(f"Network validation failed: {str(e)}")
            return False

    def validate_security_settings(self, params: Dict[str, Any]) -> bool:
        try:
            config = self.load_config('config/config.yaml')
            security_config = config['security']['shielded_instance']
            expected = params['expected']
            
            assert security_config['secure_boot'] == expected['secure_boot'], f"Secure boot setting mismatch"
            assert security_config['vtpm'] == expected['vtpm'], f"vTPM setting mismatch"
            assert security_config['integrity_monitoring'] == expected['integrity_monitoring'], f"Integrity monitoring mismatch"
            
            self.logger.info("Security configuration validation passed")
            return True
        except Exception as e:
            self.logger.error(f"Security validation failed: {str(e)}")
            return False

@pytest.mark.gcp
@pytest.mark.standalone
class TestGCPStandaloneConfig:
    
    def test_cpu_model_validation(self, config_validator):
        test_params = {
            'model': 'ice_lake_8380',
            'expected': {
                'cores': 40,
                'threads': 80,
                'base_frequency': '2.3GHz'
            }
        }
        assert config_validator.validate_cpu_model(test_params)

    def test_gpu_specs_validation(self, config_validator):
        test_params = {
            'model': 'a100',
            'expected': {
                'memory': '80GB',
                'cuda_cores': 6912,
                'tensor_cores': 432
            }
        }
        assert config_validator.validate_gpu_specs(test_params)

    def test_memory_settings_validation(self, config_validator):
        test_params = {
            'type': 'ddr5',
            'expected': {
                'speed': '4800MHz',
                'channels': 8,
                'ecc': True
            }
        }
        assert config_validator.validate_memory_settings(test_params)

    def test_network_settings_validation(self, config_validator):
        test_params = {
            'expected': {
                'network': 'standalone-vpc',
                'subnet': 'standalone-subnet',
                'ip_range': '10.0.0.0/16'
            }
        }
        assert config_validator.validate_network_settings(test_params)

    def test_security_settings_validation(self, config_validator):
        test_params = {
            'expected': {
                'secure_boot': True,
                'vtpm': True,
                'integrity_monitoring': True
            }
        }
        assert config_validator.validate_security_settings(test_params) 
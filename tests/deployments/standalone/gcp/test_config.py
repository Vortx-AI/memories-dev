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
            config = self.load_config('hardware/cpu.yaml')
            cpu_config = config['cpu']
            expected = params['expected']
            
            assert cpu_config['architecture'] == expected['architecture'], f"Architecture mismatch"
            assert cpu_config['machine_type'] == expected['machine_type'], f"Machine type mismatch"
            assert cpu_config['vcpus'] == expected['vcpus'], f"vCPU configuration mismatch"
            
            self.logger.info(f"CPU configuration validation passed")
            return True
        except Exception as e:
            self.logger.error(f"CPU model validation failed: {str(e)}")
            return False

    def validate_gpu_specs(self, params: Dict[str, Any]) -> bool:
        try:
            config = self.load_config('hardware/gpu.yaml')
            gpu_config = config['gpu']
            expected = params['expected']
            
            assert gpu_config['type'] == expected['type'], f"GPU type mismatch"
            assert gpu_config['count'] == expected['count'], f"GPU count mismatch"
            assert gpu_config['memory'] == expected['memory'], f"Memory configuration mismatch"
            assert gpu_config['cuda_version'] == expected['cuda_version'], f"CUDA version mismatch"
            
            self.logger.info(f"GPU configuration validation passed")
            return True
        except Exception as e:
            self.logger.error(f"GPU validation failed: {str(e)}")
            return False

    def validate_memory_settings(self, params: Dict[str, Any]) -> bool:
        try:
            config = self.load_config('hardware/memory.yaml')
            memory_config = config['memory']
            expected = params['expected']
            
            assert memory_config['ram'] == expected['ram'], f"RAM configuration mismatch"
            assert memory_config['persistent_disk'] == expected['persistent_disk'], f"Persistent disk configuration mismatch"
            assert memory_config['iops'] == expected['iops'], f"IOPS configuration mismatch"
            
            self.logger.info(f"Memory configuration validation passed")
            return True
        except Exception as e:
            self.logger.error(f"Memory validation failed: {str(e)}")
            return False

    def validate_network_settings(self, params: Dict[str, Any]) -> bool:
        try:
            config = self.load_config('hardware/network.yaml')
            network_config = config['network']
            expected = params['expected']
            
            assert network_config['vpc'] == expected['vpc'], f"VPC configuration mismatch"
            assert network_config['subnets'] == expected['subnets'], f"Subnet configuration mismatch"
            
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
            'expected': {
                'architecture': 'x86_64',
                'machine_type': ['n2-standard-4', 'n2-standard-8', 'n2-standard-16'],
                'vcpus': {'min': 4, 'max': 16}
            }
        }
        assert config_validator.validate_cpu_model(test_params)

    def test_gpu_specs_validation(self, config_validator):
        test_params = {
            'expected': {
                'type': 'nvidia_tesla_t4',
                'count': 1,
                'memory': {'min': 16, 'max': 64},
                'cuda_version': '11.0'
            }
        }
        assert config_validator.validate_gpu_specs(test_params)

    def test_memory_settings_validation(self, config_validator):
        test_params = {
            'expected': {
                'ram': {'min': 16, 'max': 32},
                'persistent_disk': {'enabled': True, 'type': 'pd-ssd'},
                'iops': {'baseline': 3000, 'burst': 6000}
            }
        }
        assert config_validator.validate_memory_settings(test_params)

    def test_network_settings_validation(self, config_validator):
        test_params = {
            'expected': {
                'vpc': {
                    'enabled': True,
                    'cidr': '10.0.0.0/16'
                },
                'subnets': {
                    'public': {
                        'enabled': True,
                        'cidr': '10.0.1.0/24',
                        'region': 'us-central1'
                    },
                    'private': {
                        'enabled': True,
                        'cidr': '10.0.2.0/24',
                        'region': 'us-central1'
                    }
                }
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
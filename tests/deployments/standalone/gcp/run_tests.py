#!/usr/bin/env python3

import yaml
import json
import sys
import os
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any
from google.cloud import compute_v1, monitoring_v3
from google.cloud.monitoring_v3 import AlertPolicy

class ConfigurationValidator:
    def __init__(self, config_dir: str, test_config: Dict[str, Any]):
        self.config_dir = config_dir
        self.test_config = test_config
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("ConfigValidator")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def load_config(self, config_file: str) -> Dict[str, Any]:
        with open(os.path.join(self.config_dir, config_file), 'r') as f:
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

    def run_all_tests(self) -> bool:
        results = []
        for suite_name, suite in self.test_config['test_suites'].items():
            self.logger.info(f"Running test suite: {suite_name}")
            if isinstance(suite, dict):
                for category, tests in suite.items():
                    if isinstance(tests, list):
                        for test in tests:
                            results.append(self._run_test(test))
                    elif isinstance(tests, dict):
                        for _, test_list in tests.items():
                            for test in test_list:
                                results.append(self._run_test(test))
            elif isinstance(suite, list):
                for test in suite:
                    results.append(self._run_test(test))
        
        success_rate = sum(results) / len(results) * 100
        self.logger.info(f"Test completion rate: {success_rate}%")
        return all(results)

    def _run_test(self, test: Dict[str, Any]) -> bool:
        test_name = test['name']
        test_func = getattr(self, test['test'], None)
        
        if test_func is None:
            self.logger.error(f"Test function {test['test']} not found")
            return False
        
        self.logger.info(f"Running test: {test_name}")
        try:
            result = test_func(test['params'])
            self.logger.info(f"Test {test_name}: {'PASSED' if result else 'FAILED'}")
            return result
        except Exception as e:
            self.logger.error(f"Test {test_name} failed with error: {str(e)}")
            return False

    def generate_report(self, results: List[bool]) -> None:
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(results),
            'passed_tests': sum(results),
            'failed_tests': len(results) - sum(results),
            'success_rate': f"{(sum(results) / len(results) * 100):.2f}%"
        }
        
        report_path = self.test_config['reporting']['output_dir']
        os.makedirs(report_path, exist_ok=True)
        
        report_file = os.path.join(report_path, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Test report generated: {report_file}")

def main():
    parser = argparse.ArgumentParser(description='GCP Configuration Validator')
    parser.add_argument('--config-dir', type=str, required=True, help='Path to configuration directory')
    parser.add_argument('--test-config', type=str, required=True, help='Path to test configuration file')
    args = parser.parse_args()

    with open(args.test_config, 'r') as f:
        test_config = yaml.safe_load(f)

    validator = ConfigurationValidator(args.config_dir, test_config)
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
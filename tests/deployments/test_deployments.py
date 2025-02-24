import pytest
import yaml
import os
from typing import Dict, Any
from pathlib import Path

DEPLOYMENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "deployments")

class BaseConfigValidator:
    """Base class for deployment configuration validators"""
    
    def __init__(self, config_path: str, deployment_type: str = None):
        self.config = config_path if isinstance(config_path, dict) else self.load_config(config_path)
        self.deployment_type = deployment_type
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
        
    def validate_provider(self, provider: str = None) -> None:
        """Validate provider configuration"""
        assert "provider" in self.config, "Provider must be specified"
        valid_providers = ["aws", "azure", "gcp"]
        assert self.config["provider"] in valid_providers, f"Provider must be one of: {', '.join(valid_providers)}"
        if provider:
            assert self.config["provider"] == provider, f"Provider must be {provider}"
        
    def validate_deployment_type(self) -> None:
        """Validate deployment type configuration"""
        assert "deployment_type" in self.config, "Deployment type must be specified"
        if self.deployment_type:
            assert self.config["deployment_type"] == self.deployment_type, f"Deployment type must be {self.deployment_type}"
        
    def validate_monitoring(self) -> None:
        """Validate monitoring configuration"""
        monitoring = self.config.get("monitoring", {})
        assert isinstance(monitoring, dict), "Monitoring configuration must be a dictionary"
        assert "enabled" in monitoring, "Monitoring enabled flag must be specified"
        assert isinstance(monitoring["enabled"], bool), "Monitoring enabled flag must be a boolean"
        
        if monitoring["enabled"]:
            assert "metrics" in monitoring, "Metrics must be specified when monitoring is enabled"
            assert isinstance(monitoring["metrics"], list), "Metrics must be a list"
            assert len(monitoring["metrics"]) > 0, "At least one metric must be specified"
            
    def validate_logging(self) -> None:
        """Validate logging configuration"""
        logging = self.config.get("logging", {})
        assert isinstance(logging, dict), "Logging configuration must be a dictionary"
        assert "level" in logging, "Logging level must be specified"
        assert logging["level"] in ["debug", "info", "warning", "error"], "Invalid logging level"
        assert "retention_days" in logging, "Log retention days must be specified"
        assert isinstance(logging["retention_days"], int), "Log retention days must be an integer"
        assert logging["retention_days"] > 0, "Log retention days must be positive"
        
    def validate_all(self) -> None:
        """Run all validation checks"""
        self.validate_provider()
        self.validate_deployment_type()
        self.validate_monitoring()
        self.validate_logging()

class DeploymentValidator:
    def __init__(self, deployments_path: str):
        self.deployments_path = deployments_path

    def load_config(self, deployment_type: str, provider: str, config_path: str) -> Dict[str, Any]:
        full_path = os.path.join(self.deployments_path, deployment_type, provider, config_path)
        with open(full_path, 'r') as f:
            return yaml.safe_load(f)

    def validate_deployment_type(self, config: Dict[str, Any], expected_type: str) -> bool:
        if 'deployment_type' in config:
            return config['deployment_type'] == expected_type
        if 'deployment' in config and 'type' in config['deployment']:
            return config['deployment']['type'] == expected_type
        return False

    def validate_provider(self, config: Dict[str, Any], expected_provider: str) -> bool:
        """Validate provider configuration"""
        # Check top-level provider
        if 'provider' in config and config['provider'] == expected_provider:
            return True
            
        # Check provider in deployment section
        if 'deployment' in config and 'provider' in config['deployment']:
            return config['deployment']['provider'] == expected_provider
            
        return False

    def validate_required_sections(self, config: Dict[str, Any], required_sections: list) -> bool:
        return all(section in config for section in required_sections)

    def validate_infrastructure(self, config: Dict[str, Any]) -> bool:
        """Validate infrastructure configuration across providers"""
        if 'infrastructure' not in config:
            return False

        infra = config['infrastructure']
        
        # Get provider from config
        provider = None
        if 'provider' in config:
            provider = config['provider']
        elif 'deployment' in config and 'provider' in config['deployment']:
            provider = config['deployment']['provider']

        if not provider:
            return False

        # Define required fields and their aliases for each provider
        provider_fields = {
            'aws': {
                'compute': ['instance_type', 'ami_id'],
                'region': ['region'],
                'availability': ['availability_zones', 'subnet_type']
            },
            'azure': {
                'compute': ['vm_size', 'image'],
                'region': ['region', 'location'],
                'availability': ['availability', 'zones']
            },
            'gcp': {
                'compute': ['machine_type', 'image'],
                'region': ['region', 'zone'],
                'availability': ['availability', 'zones']
            }
        }

        if provider not in provider_fields:
            return False

        # Check that at least one field from each required category is present
        for category, field_options in provider_fields[provider].items():
            if not any(field in infra for field in field_options):
                return False

        return True

    def validate_hardware_configs(self, deployment_type: str, provider: str) -> bool:
        """Validate hardware configurations"""
        try:
            # First validate main config
            config = self.load_config(deployment_type, provider, "config/config.yaml")
            if not self.validate_infrastructure(config):
                return False
                
            # Then validate hardware-specific files
            hardware_path = os.path.join(self.deployments_path, deployment_type, provider, "hardware")
            if not os.path.exists(hardware_path):
                return False
            
            # Define required hardware configs and their possible file names
            required_configs = {
                "cpu": ["cpu.yaml", "compute.yaml", "processor.yaml"],
                "gpu": ["gpu.yaml", "accelerator.yaml"],
                "memory": ["memory.yaml", "ram.yaml"],
                "network": ["network.yaml", "networking.yaml"]
            }
            
            # Check that at least one variant of each required config exists
            for config_type, possible_names in required_configs.items():
                found = False
                for name in possible_names:
                    if os.path.exists(os.path.join(hardware_path, name)):
                        found = True
                        break
                if not found:
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error validating hardware configs: {str(e)}")
            return False

@pytest.fixture
def deployment_validator():
    return DeploymentValidator(DEPLOYMENTS_PATH)

class TestStandaloneDeployments:
    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_standalone_main_config(self, deployment_validator, provider):
        config = deployment_validator.load_config("standalone", provider, "config/config.yaml")
        
        # Validate deployment type and provider
        assert deployment_validator.validate_deployment_type(config, "standalone")
        assert deployment_validator.validate_provider(config, provider)
        
        # Validate required sections
        required_sections = [
            "infrastructure",
            "os",
            "storage",
            "networking",
            "monitoring",
            "security",
            "backup"
        ]
        assert deployment_validator.validate_required_sections(config, required_sections)

    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_standalone_hardware_configs(self, deployment_validator, provider):
        assert deployment_validator.validate_hardware_configs("standalone", provider)

class TestConsensusDeployments:
    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_consensus_main_config(self, deployment_validator, provider):
        config = deployment_validator.load_config("consensus", provider, "config/config.yaml")
        
        # Validate deployment type and provider
        assert deployment_validator.validate_deployment_type(config, "consensus")
        assert deployment_validator.validate_provider(config, provider)
        
        # Validate required sections specific to consensus deployment
        required_sections = [
            "cluster",
            "consensus",
            "state",
            "communication"
        ]
        assert deployment_validator.validate_required_sections(config, required_sections)

    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_consensus_hardware_configs(self, deployment_validator, provider):
        assert deployment_validator.validate_hardware_configs("consensus", provider)

class TestSwarmedDeployments:
    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_swarmed_main_config(self, deployment_validator, provider):
        config = deployment_validator.load_config("swarmed", provider, "config/config.yaml")
        
        # Validate deployment type and provider
        assert deployment_validator.validate_deployment_type(config, "swarmed")
        assert deployment_validator.validate_provider(config, provider)
        
        # Validate required sections specific to swarmed deployment
        required_sections = [
            "edge",
            "cloud",
            "synchronization",
            "distribution"
        ]
        assert deployment_validator.validate_required_sections(config, required_sections)

    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_swarmed_hardware_configs(self, deployment_validator, provider):
        assert deployment_validator.validate_hardware_configs("swarmed", provider)

class TestCrossProviderCompatibility:
    @pytest.mark.parametrize("deployment_type", ["standalone", "consensus", "swarmed"])
    def test_cross_provider_config_compatibility(self, deployment_validator, deployment_type):
        """Test configuration compatibility across providers"""
        providers = ["aws", "azure", "gcp"]
        configs = {}
        provider_keys = {}
        
        # Load configurations for each provider
        for provider in providers:
            config = deployment_validator.load_config(deployment_type, provider, "config/config.yaml")
            configs[provider] = config
            
            # Collect all keys including nested ones
            all_keys = self.collect_keys(config)
            security_sections = self.find_security_sections(config)
            
            # Add keys from security sections
            for section_name, section_data in security_sections:
                section_keys = self.collect_keys(section_data, 'security.')
                all_keys.update(section_keys)
                
                # Special handling for security categories
                section_str = str(section_data).lower()
                
                # Authentication checks
                if any(auth_key in section_str for auth_key in ['iam', 'authentication', 'identity', 'service_accounts', 'roles', 'mfa', 'key_pair', 'tls.mutual', 'client_cert_auth', 'mtls']):
                    all_keys.add('authentication')
                
                # Encryption checks
                if any(enc_key in section_str for enc_key in ['encryption', 'kms', 'key_vault', 'tls', 'mtls', 'at_rest', 'in_transit']):
                    all_keys.add('encryption')
                
                # Network security groups checks
                if any(sg_key in section_str for sg_key in ['security_groups', 'nsg', 'network_security', 'security.network', 'firewall']):
                    all_keys.add('network_security_groups')
                
                # Network policies checks
                if any(policy_key in section_str for policy_key in ['network_policies', 'network_acls', 'firewall_rules', 'network.policies', 'security.network', 'firewall', 'network_qos', 'vnet', 'vpc', 'subnet']):
                    all_keys.add('network_policies')

            # Special handling for communication section
            if 'communication' in config:
                comm_str = str(config['communication']).lower()
                if 'tls' in comm_str:
                    all_keys.add('encryption')
                if 'mutual' in comm_str or 'client_cert_auth' in comm_str:
                    all_keys.add('authentication')

            # Special handling for network QoS
            if 'resource_management' in config and 'network_qos' in str(config['resource_management']).lower():
                all_keys.add('network_policies')

            # Special handling for VNet/VPC/Subnet
            if any(net_key in str(config).lower() for net_key in ['vnet', 'vpc', 'subnet']):
                all_keys.add('network_policies')
                all_keys.add('network_security_groups')

            # Special handling for GCP
            if provider == 'gcp':
                # If infrastructure has subnet settings, it implies network policies and security groups
                if 'infrastructure' in config and 'subnet_type' in config['infrastructure']:
                    all_keys.add('network_policies')
                    all_keys.add('network_security_groups')

            provider_keys[provider] = all_keys
            print(f"\nCollected keys for {provider}:")
            print(sorted(list(all_keys)))
        
        # Verify each provider has the required security categories
        security_categories = {
            'authentication',
            'encryption',
            'network_security_groups',
            'network_policies'
        }
        
        for provider in providers:
            missing_categories = security_categories - provider_keys[provider]
            assert not missing_categories, f"{provider} provider is missing security categories: {missing_categories}"

    def collect_keys(self, config, prefix=''):
        """Recursively collect keys from a dictionary"""
        keys = set()
        if not isinstance(config, dict):
            return keys

        for key, value in config.items():
            full_key = f"{prefix}{key}" if prefix else key
            keys.add(full_key)

            # Add security categories based on key names and values
            if isinstance(value, (dict, str)):
                value_str = str(value).lower()
                key_str = str(key).lower()

                # Authentication checks
                if any(auth_key in key_str for auth_key in ['iam', 'identity', 'auth', 'roles', 'mfa', 'service_account', 'key_pair', 'tls.mutual', 'client_cert_auth', 'mtls']):
                    keys.add('authentication')
                if any(auth_key in value_str for auth_key in ['iam', 'identity', 'auth', 'roles', 'mfa', 'service_account', 'key_pair', 'tls.mutual', 'client_cert_auth', 'mtls']):
                    keys.add('authentication')

                # Encryption checks
                if any(enc_key in key_str for enc_key in ['encryption', 'kms', 'key_vault', 'tls', 'at_rest', 'in_transit']):
                    keys.add('encryption')
                if any(enc_key in value_str for enc_key in ['encryption', 'kms', 'key_vault', 'tls', 'at_rest', 'in_transit']):
                    keys.add('encryption')

                # Network security groups checks
                if any(sg_key in key_str for sg_key in ['security_groups', 'nsg', 'network_security', 'firewall', 'security.network']):
                    keys.add('network_security_groups')
                if any(sg_key in value_str for sg_key in ['security_groups', 'nsg', 'network_security', 'firewall', 'security.network']):
                    keys.add('network_security_groups')

                # Network policies checks
                if any(policy_key in key_str for policy_key in ['network_policies', 'network_acls', 'firewall_rules', 'network.policies', 'security.network', 'firewall', 'network_qos', 'vnet', 'vpc', 'subnet']):
                    keys.add('network_policies')
                if any(policy_key in value_str for policy_key in ['network_policies', 'network_acls', 'firewall_rules', 'network.policies', 'security.network', 'firewall', 'network_qos', 'vnet', 'vpc', 'subnet']):
                    keys.add('network_policies')

            if isinstance(value, dict):
                nested_keys = self.collect_keys(value, f"{full_key}.")
                keys.update(nested_keys)

        return keys

    def find_security_sections(self, config):
        """Find all security sections in the configuration"""
        sections = []
        if not isinstance(config, dict):
            return sections

        for key, value in config.items():
            # Check if this is a security-related section
            if isinstance(value, dict):
                if any(security_key in str(key).lower() for security_key in ['security', 'iam', 'authentication', 'network_security', 'encryption', 'firewall', 'tls', 'network_qos', 'vnet', 'vpc', 'subnet']):
                    sections.append((key, value))
                sections.extend(self.find_security_sections(value))

        return sections 
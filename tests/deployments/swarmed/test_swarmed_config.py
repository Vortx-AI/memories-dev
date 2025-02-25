import pytest
import yaml
import os
import logging
from typing import Dict, Any

from tests.deployments.test_deployments import BaseConfigValidator

DEPLOYMENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "deployments")

class SwarmedConfigValidator(BaseConfigValidator):
    """Validator for swarmed deployment configurations"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.deployment_type = "swarmed"
        
    def validate_swarm_settings(self) -> None:
        """Validate swarm-specific settings"""
        assert "swarm" in self.config, "Swarm settings not found"
        swarm = self.config["swarm"]
        
        assert "manager_nodes" in swarm, "manager_nodes not specified"
        assert isinstance(swarm["manager_nodes"], int), "manager_nodes must be an integer"
        assert swarm["manager_nodes"] >= 3, "manager_nodes must be at least 3"
        
        assert "worker_nodes" in swarm, "worker_nodes not specified"
        assert isinstance(swarm["worker_nodes"], int), "worker_nodes must be an integer"
        assert swarm["worker_nodes"] > 0, "worker_nodes must be positive"

    def validate_node_specs(self):
        """Validate node specifications"""
        assert "node_specs" in self.config, "Node specifications not found"
        specs = self.config["node_specs"]
        
        for node_type in ["manager", "worker"]:
            assert f"{node_type}_specs" in specs, f"{node_type} specifications not found"
            type_specs = specs[f"{node_type}_specs"]
            
            assert "instance_type" in type_specs, f"{node_type} instance_type not specified"
            assert isinstance(type_specs["instance_type"], str), f"{node_type} instance_type must be a string"
            
            assert "storage_size" in type_specs, f"{node_type} storage_size not specified"
            assert isinstance(type_specs["storage_size"], int), f"{node_type} storage_size must be an integer"
            assert type_specs["storage_size"] > 0, f"{node_type} storage_size must be positive"

    def validate_network_config(self):
        """Validate network configuration"""
        assert "network" in self.config, "Network configuration not found"
        network = self.config["network"]
        
        assert "vpc_cidr" in network, "vpc_cidr not specified"
        assert isinstance(network["vpc_cidr"], str), "vpc_cidr must be a string"
        
        assert "subnet_type" in network, "subnet_type not specified"
        assert network["subnet_type"] in ["private", "public"], "subnet_type must be private or public"
        
        assert "security_group" in network, "security_group not found"
        sg = network["security_group"]
        assert "rules" in sg, "security group rules not specified"
        assert isinstance(sg["rules"], list), "security group rules must be a list"
        
        # Validate Docker Swarm specific ports are allowed
        required_ports = [2377, 7946, 4789]  # TCP ports for swarm management, container network discovery
        allowed_ports = set()
        for rule in sg["rules"]:
            if "port" in rule:
                allowed_ports.add(rule["port"])
        
        for port in required_ports:
            assert port in allowed_ports, f"Required port {port} not allowed in security group rules"

    def validate_all(self) -> None:
        """Run all validation checks"""
        super().validate_all()
        self.validate_swarm_settings()
        self.validate_node_specs()
        self.validate_network_config()

@pytest.fixture
def aws_swarmed_config(test_data_dir: str) -> Dict[Any, Any]:
    """Load AWS swarmed configuration for testing"""
    config_path = os.path.join(test_data_dir, "aws_swarmed.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)

@pytest.fixture
def azure_swarmed_config(test_data_dir: str) -> Dict[Any, Any]:
    """Load Azure swarmed configuration for testing"""
    config_path = os.path.join(test_data_dir, "azure_swarmed.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)

@pytest.fixture
def gcp_swarmed_config(test_data_dir: str) -> Dict[Any, Any]:
    """Load GCP swarmed configuration for testing"""
    config_path = os.path.join(test_data_dir, "gcp_swarmed.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)

@pytest.fixture
def aws_config_validator(test_data_dir: str) -> BaseConfigValidator:
    """Create AWS config validator for testing"""
    config_path = os.path.join(test_data_dir, "aws_swarmed.yaml")
    return BaseConfigValidator(config_path, deployment_type="swarmed")

@pytest.fixture
def azure_config_validator(test_data_dir: str) -> BaseConfigValidator:
    """Create Azure config validator for testing"""
    config_path = os.path.join(test_data_dir, "azure_swarmed.yaml")
    return BaseConfigValidator(config_path, deployment_type="swarmed")

@pytest.fixture
def gcp_config_validator(test_data_dir: str) -> BaseConfigValidator:
    """Create GCP config validator for testing"""
    config_path = os.path.join(test_data_dir, "gcp_swarmed.yaml")
    return BaseConfigValidator(config_path, deployment_type="swarmed")

class TestSwarmedConfig:
    """Test cases for swarmed deployment configurations"""
    
    @pytest.fixture
    def test_data_dir(self):
        return os.path.join(os.path.dirname(__file__), "../../test_data/swarmed")

    def test_aws_swarmed_config(self, aws_config_validator):
        """Test AWS swarmed configuration"""
        aws_config_validator.validate_provider("aws")
        aws_config_validator.validate_deployment_type()
        # Additional swarmed-specific validations
        assert "swarm" in aws_config_validator.config
        swarm_config = aws_config_validator.config["swarm"]
        assert "manager_nodes" in swarm_config
        assert swarm_config["manager_nodes"] >= 3
        assert "worker_nodes" in swarm_config
        assert swarm_config["worker_nodes"] >= 1

    def test_azure_swarmed_config(self, azure_config_validator):
        """Test Azure swarmed configuration"""
        azure_config_validator.validate_provider("azure")
        azure_config_validator.validate_deployment_type()
        # Additional swarmed-specific validations
        assert "swarm" in azure_config_validator.config
        swarm_config = azure_config_validator.config["swarm"]
        assert "manager_nodes" in swarm_config
        assert swarm_config["manager_nodes"] >= 3
        assert "worker_nodes" in swarm_config
        assert swarm_config["worker_nodes"] >= 1

    def test_gcp_swarmed_config(self, gcp_config_validator):
        """Test GCP swarmed configuration"""
        gcp_config_validator.validate_provider("gcp")
        gcp_config_validator.validate_deployment_type()
        # Additional swarmed-specific validations
        assert "swarm" in gcp_config_validator.config
        swarm_config = gcp_config_validator.config["swarm"]
        assert "manager_nodes" in swarm_config
        assert swarm_config["manager_nodes"] >= 3
        assert "worker_nodes" in swarm_config
        assert swarm_config["worker_nodes"] >= 1

    def test_invalid_swarm_settings(self, aws_swarmed_config: Dict[Any, Any]) -> None:
        """Test validation of invalid swarm settings"""
        config = aws_swarmed_config.copy()
        config["swarm"]["manager_nodes"] = 2
        
        validator = SwarmedConfigValidator(config)
        with pytest.raises(AssertionError, match="manager_nodes must be at least 3"):
            validator.validate_all()
            
    def test_invalid_node_configuration(self, aws_swarmed_config: Dict[Any, Any]) -> None:
        """Test validation of invalid node configuration"""
        config = aws_swarmed_config.copy()
        del config["node_specs"]["manager_specs"]["instance_type"]
        
        validator = SwarmedConfigValidator(config)
        with pytest.raises(AssertionError, match="manager instance_type not specified"):
            validator.validate_all() 
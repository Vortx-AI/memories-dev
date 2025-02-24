import pytest
import yaml
import os
import logging
from typing import Dict, Any

from tests.deployments.test_deployments import BaseConfigValidator

DEPLOYMENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "deployments")

class ConsensusConfigValidator(BaseConfigValidator):
    """Validator for consensus deployment configurations"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.deployment_type = "consensus"
        
    def validate_consensus_settings(self) -> None:
        """Validate consensus-specific settings"""
        assert "consensus" in self.config, "Consensus settings not found"
        consensus = self.config["consensus"]
        
        assert "min_nodes" in consensus, "min_nodes not specified"
        assert isinstance(consensus["min_nodes"], int), "min_nodes must be an integer"
        assert consensus["min_nodes"] >= 3, "min_nodes must be at least 3"
        
        assert "max_nodes" in consensus, "max_nodes not specified"
        assert isinstance(consensus["max_nodes"], int), "max_nodes must be an integer"
        assert consensus["max_nodes"] >= consensus["min_nodes"], "max_nodes must be >= min_nodes"
        
        assert "algorithm" in consensus, "consensus algorithm not specified"
        assert consensus["algorithm"] in ["raft", "paxos"], "algorithm must be raft or paxos"
        
        assert "quorum_size" in consensus, "quorum_size not specified"
        assert isinstance(consensus["quorum_size"], int), "quorum_size must be an integer"
        assert consensus["quorum_size"] <= consensus["min_nodes"], "quorum_size must be <= min_nodes"

    def validate_node_specs(self):
        """Validate node specifications"""
        assert "node_specs" in self.config, "Node specifications not found"
        specs = self.config["node_specs"]
        
        assert "instance_type" in specs, "instance_type not specified"
        assert isinstance(specs["instance_type"], str), "instance_type must be a string"
        
        assert "storage_size" in specs, "storage_size not specified"
        assert isinstance(specs["storage_size"], int), "storage_size must be an integer"
        assert specs["storage_size"] > 0, "storage_size must be positive"

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

    def validate_all(self) -> None:
        """Run all validation checks"""
        super().validate_all()
        self.validate_consensus_settings()
        self.validate_node_specs()
        self.validate_network_config()

@pytest.fixture
def test_data_dir():
    return os.path.join(os.path.dirname(__file__), "..", "..", "test_data", "consensus")

@pytest.fixture
def aws_config_validator(test_data_dir: str) -> BaseConfigValidator:
    """Create AWS config validator for testing"""
    config_path = os.path.join(test_data_dir, "consensus", "aws_consensus.yaml")
    return BaseConfigValidator(config_path, deployment_type="consensus")

@pytest.fixture
def azure_config_validator(test_data_dir: str) -> BaseConfigValidator:
    """Create Azure config validator for testing"""
    config_path = os.path.join(test_data_dir, "consensus", "azure_consensus.yaml")
    return BaseConfigValidator(config_path, deployment_type="consensus")

@pytest.fixture
def gcp_config_validator(test_data_dir: str) -> BaseConfigValidator:
    """Create GCP config validator for testing"""
    config_path = os.path.join(test_data_dir, "consensus", "gcp_consensus.yaml")
    return BaseConfigValidator(config_path, deployment_type="consensus")

class TestConsensusConfig:
    """Test cases for consensus deployment configurations"""
    
    def test_aws_config(self, aws_config_validator):
        """Test AWS consensus configuration"""
        aws_config_validator.validate_all()

    def test_azure_config(self, azure_config_validator):
        """Test Azure consensus configuration"""
        azure_config_validator.validate_all()

    def test_gcp_config(self, gcp_config_validator):
        """Test GCP consensus configuration"""
        gcp_config_validator.validate_all()

    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_invalid_min_nodes(self, test_data_dir, provider):
        """Test validation fails with invalid min_nodes"""
        config_path = os.path.join(test_data_dir, f"{provider}_consensus.yaml")
        validator = ConsensusConfigValidator(config_path)
        validator.config["consensus"]["min_nodes"] = 2
        with pytest.raises(AssertionError, match="min_nodes must be at least 3"):
            validator.validate_consensus_settings()

    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_invalid_algorithm(self, test_data_dir, provider):
        """Test validation fails with invalid consensus algorithm"""
        config_path = os.path.join(test_data_dir, f"{provider}_consensus.yaml")
        validator = ConsensusConfigValidator(config_path)
        validator.config["consensus"]["algorithm"] = "invalid"
        with pytest.raises(AssertionError, match="algorithm must be raft or paxos"):
            validator.validate_consensus_settings()

    @pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
    def test_invalid_quorum_size(self, test_data_dir, provider):
        """Test validation fails with invalid quorum size"""
        config_path = os.path.join(test_data_dir, f"{provider}_consensus.yaml")
        validator = ConsensusConfigValidator(config_path)
        validator.config["consensus"]["quorum_size"] = 10
        with pytest.raises(AssertionError, match="quorum_size must be <= min_nodes"):
            validator.validate_consensus_settings()

    @pytest.fixture
    def test_data_dir(self):
        return os.path.join(os.path.dirname(__file__), "../../test_data/consensus")

    @pytest.fixture
    def aws_config_validator(self, test_data_dir):
        config_path = os.path.join(test_data_dir, "aws_consensus.yaml")
        return BaseConfigValidator(config_path)

    @pytest.fixture
    def azure_config_validator(self, test_data_dir):
        config_path = os.path.join(test_data_dir, "azure_consensus.yaml")
        return BaseConfigValidator(config_path)

    @pytest.fixture
    def gcp_config_validator(self, test_data_dir):
        config_path = os.path.join(test_data_dir, "gcp_consensus.yaml")
        return BaseConfigValidator(config_path)

    def test_aws_consensus_config(self, aws_config_validator):
        """Test AWS consensus configuration"""
        aws_config_validator.validate_provider("aws")
        aws_config_validator.validate_deployment_type()
        # Additional consensus-specific validations
        assert "consensus" in aws_config_validator.config
        consensus_config = aws_config_validator.config["consensus"]
        assert "algorithm" in consensus_config
        assert consensus_config["algorithm"] in ["raft", "paxos"]

    def test_azure_consensus_config(self, azure_config_validator):
        """Test Azure consensus configuration"""
        azure_config_validator.validate_provider("azure")
        azure_config_validator.validate_deployment_type()
        # Additional consensus-specific validations
        assert "consensus" in azure_config_validator.config
        consensus_config = azure_config_validator.config["consensus"]
        assert "algorithm" in consensus_config
        assert consensus_config["algorithm"] in ["raft", "paxos"]

    def test_gcp_consensus_config(self, gcp_config_validator):
        """Test GCP consensus configuration"""
        gcp_config_validator.validate_provider("gcp")
        gcp_config_validator.validate_deployment_type()
        # Additional consensus-specific validations
        assert "consensus" in gcp_config_validator.config
        consensus_config = gcp_config_validator.config["consensus"]
        assert "algorithm" in consensus_config
        assert consensus_config["algorithm"] in ["raft", "paxos"] 
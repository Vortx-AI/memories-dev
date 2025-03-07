"""Tests for the LoadModel class."""

import pytest
from unittest.mock import Mock, patch
from memories.models.load_model import LoadModel
from memories.models.base_model import BaseModel

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "models": {
            "test-model": {
                "name": "test/model",
                "provider": "test-provider",
                "type": "api",
                "config": {
                    "max_length": 1000,
                    "temperature": 0.7
                }
            }
        },
        "supported_providers": ["test-provider", "openai", "anthropic", "deepseek"],
        "deployment_types": ["api", "local"],
        "default_model": "test-model"
    }

@pytest.fixture
def mock_api_connector():
    """Mock API connector for testing."""
    connector = Mock()
    connector.generate.return_value = "Test response"
    return connector

@pytest.fixture
def mock_base_model():
    """Mock BaseModel for testing."""
    model = Mock()
    model.generate.return_value = "Test response"
    return model

@patch("memories.models.load_model.get_connector")
def test_init_api_model(mock_get_connector, mock_api_connector):
    """Test initialization of API-based model."""
    mock_get_connector.return_value = mock_api_connector
    
    model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4",
        api_key="test-key"
    )
    
    assert model.model_provider == "openai"
    assert model.deployment_type == "api"
    assert model.model_name == "gpt-4"
    assert model.api_key == "test-key"
    mock_get_connector.assert_called_once_with("openai", "test-key", None)

@patch("memories.models.load_model.BaseModel")
def test_init_local_model(mock_base_model_class):
    """Test initialization of local model."""
    mock_base_model = Mock()
    mock_base_model_class.get_instance.return_value = mock_base_model
    mock_base_model.initialize_model.return_value = True

    model = LoadModel(
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small",
        use_gpu=False
    )

    assert model is not None
    mock_base_model.initialize_model.assert_called_once_with(
        model="deepseek-coder-small",
        use_gpu=False,
        device=None
    )

def test_init_invalid_deployment_type():
    """Test initialization with invalid deployment type."""
    with pytest.raises(ValueError):
        LoadModel(
            model_provider="openai",
            deployment_type="invalid",
            model_name="gpt-4"
        )

def test_init_invalid_provider():
    """Test initialization with invalid provider."""
    with pytest.raises(ValueError):
        LoadModel(
            model_provider="invalid",
            deployment_type="api",
            model_name="gpt-4"
        )

def test_init_missing_api_key():
    """Test initialization without API key for API deployment."""
    with pytest.raises(ValueError):
        LoadModel(
            model_provider="openai",
            deployment_type="api",
            model_name="gpt-4"
        )

@patch("memories.models.load_model.get_connector")
def test_get_response_api(mock_get_connector, mock_api_connector):
    """Test getting response from API model."""
    mock_get_connector.return_value = mock_api_connector
    mock_api_connector.generate.return_value = {
        "text": "Test response",
        "error": None,
        "metadata": {
            "attempt": 1,
            "generation_time": 0,
            "total_tokens": 0
        }
    }
    
    model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4",
        api_key="test-key"
    )
    
    response = model.get_response("Test prompt")
    assert isinstance(response, dict)
    assert response["text"] == "Test response"
    assert response["error"] is None
    assert "metadata" in response
    mock_api_connector.generate.assert_called_once_with("Test prompt", timeout=30)

@patch("memories.models.load_model.BaseModel")
def test_get_response_local(mock_base_model_class):
    """Test getting response from local model."""
    mock_base_model = Mock()
    mock_base_model_class.get_instance.return_value = mock_base_model
    mock_base_model.initialize_model.return_value = True
    mock_base_model.generate.return_value = "Test response"

    model = LoadModel(
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small"
    )

    response = model.get_response("Test prompt")
    assert response["text"] == "Test response"
    assert response["error"] is None
    assert "metadata" in response
    mock_base_model.generate.assert_called_once_with("Test prompt", timeout=30)

@patch("memories.models.load_model.get_connector")
def test_get_response_with_params(mock_get_connector, mock_api_connector):
    """Test getting response with additional parameters."""
    mock_get_connector.return_value = mock_api_connector
    mock_api_connector.generate.return_value = {
        "text": "Test response",
        "error": None,
        "metadata": {
            "attempt": 1,
            "generation_time": 0,
            "total_tokens": 0
        }
    }
    
    model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4",
        api_key="test-key"
    )
    
    params = {
        "temperature": 0.8,
        "max_tokens": 100
    }
    
    response = model.get_response("Test prompt", **params)
    assert isinstance(response, dict)
    assert response["text"] == "Test response"
    assert response["error"] is None
    assert "metadata" in response
    mock_api_connector.generate.assert_called_once_with("Test prompt", timeout=30, **params)

def test_cleanup():
    """Test cleanup method."""
    with patch("memories.models.load_model.BaseModel") as mock_base_model_class:
        mock_base_model = Mock()
        mock_base_model_class.get_instance.return_value = mock_base_model
        mock_base_model.initialize_model.return_value = True

        model = LoadModel(
            model_provider="deepseek-ai",
            deployment_type="local",
            model_name="deepseek-coder-small"
        )

        model.cleanup()
        mock_base_model.cleanup.assert_called_once() 
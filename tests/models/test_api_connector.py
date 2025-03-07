"""Tests for the API connectors."""

import pytest
from unittest.mock import Mock, patch
import importlib
from memories.models.api_connector import (
    APIConnector,
    OpenAIConnector,
    DeepseekConnector,
    get_connector
)

def is_package_installed(package_name):
    """Check if a package is installed."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return Mock(choices=[Mock(message=Mock(content="Test response"))])

@pytest.fixture
def mock_deepseek_response():
    """Mock Deepseek API response."""
    return {
        "choices": [
            {"message": {"content": "Test response"}}
        ]
    }

@pytest.mark.skipif(not is_package_installed("openai"), reason="openai package not installed")
@patch("openai.OpenAI")
def test_get_connector_openai(mock_openai):
    """Test getting OpenAI connector."""
    connector = get_connector("openai", "test-key")
    assert isinstance(connector, OpenAIConnector)
    assert connector.api_key == "test-key"

def test_get_connector_deepseek():
    """Test getting Deepseek connector."""
    connector = get_connector("deepseek", "test-key")
    assert isinstance(connector, DeepseekConnector)
    assert connector.api_key == "test-key"

def test_get_connector_invalid():
    """Test getting invalid connector."""
    with pytest.raises(ValueError):
        get_connector("invalid-provider", "test-key")

@pytest.mark.skipif(not is_package_installed("openai"), reason="openai package not installed")
@patch("openai.OpenAI")
def test_openai_generate(mock_openai, mock_openai_response):
    """Test OpenAI text generation."""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai.return_value = mock_client

    connector = OpenAIConnector("test-key")
    response = connector.generate("Test prompt")
    
    assert response == "Test response"
    mock_client.chat.completions.create.assert_called_once()

@patch("requests.post")
def test_deepseek_generate(mock_post, mock_deepseek_response):
    """Test Deepseek text generation."""
    mock_response = Mock()
    mock_response.json.return_value = mock_deepseek_response
    mock_post.return_value = mock_response

    connector = DeepseekConnector("test-key")
    response = connector.generate("Test prompt")
    
    assert response == "Test response"
    mock_post.assert_called_once()

@pytest.mark.skipif(not is_package_installed("openai"), reason="openai package not installed")
@patch("openai.OpenAI")
def test_openai_error_handling(mock_openai):
    """Test OpenAI error handling."""
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    connector = OpenAIConnector("test-key")
    with pytest.raises(Exception):
        connector.generate("Test prompt")

def test_deepseek_error_handling():
    """Test Deepseek error handling."""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("API Error")

        connector = DeepseekConnector("test-key")
        with pytest.raises(Exception):
            connector.generate("Test prompt")

@pytest.mark.parametrize("provider,env_var", [
    pytest.param("openai", "OPENAI_API_KEY", marks=pytest.mark.skipif(not is_package_installed("openai"), reason="openai package not installed")),
    ("deepseek", "DEEPSEEK_API_KEY")
])
def test_api_key_from_env(provider, env_var, monkeypatch):
    """Test getting API key from environment variables."""
    monkeypatch.setenv(env_var, "test-key")
    
    if provider == "openai" and is_package_installed("openai"):
        with patch("openai.OpenAI") as mock_openai:
            connector = get_connector(provider)
            assert connector.api_key == "test-key"
    else:
        connector = get_connector(provider)
        assert connector.api_key == "test-key" 
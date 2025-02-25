"""Tests for the BaseModel class."""

import pytest
import torch
from unittest.mock import Mock, patch, MagicMock
import gc
from memories.models.base_model import BaseModel

@pytest.fixture
def base_model():
    """Create a BaseModel instance for testing."""
    return BaseModel.get_instance()

def test_singleton_instance():
    """Test that BaseModel follows singleton pattern."""
    model1 = BaseModel.get_instance()
    model2 = BaseModel.get_instance()
    assert model1 is model2

def test_load_config():
    """Test configuration loading."""
    model = BaseModel.get_instance()
    config = model._load_config()
    assert isinstance(config, dict)
    assert "models" in config
    assert "supported_providers" in config
    assert "deployment_types" in config

@pytest.mark.parametrize("model_name", ["deepseek-coder-small", "llama-2-7b"])
def test_get_model_config(base_model, model_name):
    """Test getting configuration for specific models."""
    config = base_model.get_model_config(model_name)
    assert isinstance(config, dict)
    assert "name" in config
    assert "provider" in config
    assert "config" in config

@patch("transformers.AutoModelForCausalLM.from_pretrained")
@patch("transformers.AutoTokenizer.from_pretrained")
def test_initialize_model(mock_tokenizer, mock_model, base_model):
    """Test model initialization."""
    mock_model.return_value = Mock()
    mock_tokenizer.return_value = Mock()
    
    success = base_model.initialize_model("deepseek-coder-small", use_gpu=False)
    assert success
    mock_model.assert_called_once()
    mock_tokenizer.assert_called_once()

@patch("transformers.AutoModelForCausalLM.from_pretrained")
@patch("transformers.AutoTokenizer.from_pretrained")
def test_generate_text(mock_tokenizer, mock_model, base_model):
    """Test text generation."""
    # Create mock tokenizer
    mock_tokenizer_instance = Mock()
    mock_tokenizer.return_value = mock_tokenizer_instance

    # Create mock tensors
    input_ids = torch.tensor([[1, 2, 3]])
    attention_mask = torch.tensor([[1, 1, 1]])

    # Create a dictionary for tokenizer output with to() method
    class TokenizerOutput(dict):
        def __init__(self, input_ids, attention_mask):
            super().__init__()
            self['input_ids'] = input_ids
            self['attention_mask'] = attention_mask

        def to(self, device):
            return self

        def items(self):
            return [('input_ids', self['input_ids']), ('attention_mask', self['attention_mask'])]

    tokenizer_output = TokenizerOutput(input_ids, attention_mask)

    # Set up the tokenizer mock to return the TokenizerOutput directly
    mock_tokenizer_instance.side_effect = lambda *args, **kwargs: tokenizer_output
    mock_tokenizer_instance.decode.return_value = "print('Hello, World!')"
    mock_tokenizer_instance.eos_token_id = 2

    # Set up model mock
    mock_model_instance = Mock()
    mock_model.return_value = mock_model_instance
    mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
    mock_model_instance.to.return_value = mock_model_instance
    mock_model_instance.device = torch.device("cpu")
    mock_model_instance.config._name_or_path = "deepseek-coder-small"

    # Initialize model
    base_model.initialize_model("deepseek-coder-small", use_gpu=False)

    # Test generate
    result = base_model.generate("def factorial(n):")

    # Verify
    assert mock_tokenizer_instance.decode.call_count == 1
    decode_args = mock_tokenizer_instance.decode.call_args[0][0]
    assert torch.equal(decode_args, torch.tensor([1, 2, 3]))
    assert mock_tokenizer_instance.decode.call_args[1] == {'skip_special_tokens': True}
    mock_model_instance.generate.assert_called_once()
    assert result == "print('Hello, World!')"

@patch("transformers.AutoModelForCausalLM.from_pretrained")
@patch("transformers.AutoTokenizer.from_pretrained")
def test_gpu_support(mock_tokenizer, mock_model, base_model):
    """Test GPU support."""
    mock_model_instance = Mock()
    mock_model_instance.device = torch.device("cpu")
    mock_model_instance.to = lambda device: mock_model_instance
    mock_model.return_value = mock_model_instance
    mock_tokenizer.return_value = Mock()

    if torch.cuda.is_available():
        success = base_model.initialize_model("deepseek-coder-small", use_gpu=True)
        assert success
        assert base_model.model.device.type == "cuda"
    else:
        success = base_model.initialize_model("deepseek-coder-small", use_gpu=True)
        assert success
        assert base_model.model.device.type == "cpu"

def test_cleanup(base_model):
    """Test cleanup method."""
    with patch("transformers.AutoModelForCausalLM.from_pretrained") as mock_model:
        with patch("transformers.AutoTokenizer.from_pretrained") as mock_tokenizer:
            mock_model.return_value = Mock()
            mock_tokenizer.return_value = Mock()
            
            base_model.initialize_model("deepseek-coder-small", use_gpu=False)
            assert base_model.model is not None
            assert base_model.tokenizer is not None
            
            base_model.cleanup()
            assert base_model.model is None
            assert base_model.tokenizer is None

@pytest.mark.parametrize("provider", ["deepseek-ai", "meta", "mistral"])
def test_list_models_by_provider(base_model, provider):
    """Test listing models by provider."""
    models = base_model.list_models(provider)
    assert isinstance(models, list)
    assert len(models) > 0
    for model in models:
        config = base_model.get_model_config(model)
        assert config["provider"] == provider

def test_list_providers(base_model):
    """Test listing available providers."""
    providers = base_model.list_providers()
    assert isinstance(providers, list)
    assert len(providers) > 0
    assert "deepseek-ai" in providers
    assert "meta" in providers
    assert "mistral" in providers 
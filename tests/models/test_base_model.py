"""Tests for the BaseModel class."""

import pytest
import torch
from unittest.mock import Mock, patch
import gc
from memories.models.base_model import BaseModel

@pytest.fixture
def base_model():
    """Fixture to create a BaseModel instance."""
    model = BaseModel.get_instance()
    yield model
    model.cleanup()
    # Force garbage collection after cleanup
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

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

@patch("torch.cuda.is_available")
@patch("transformers.AutoModelForCausalLM.from_pretrained")
@patch("transformers.AutoTokenizer.from_pretrained")
def test_initialize_model_cpu(mock_tokenizer, mock_model, mock_cuda, base_model):
    """Test model initialization on CPU."""
    mock_cuda.return_value = False
    mock_model.return_value = Mock()
    mock_tokenizer.return_value = Mock()
    
    try:
        success = base_model.initialize_model("deepseek-coder-small", use_gpu=False)
        assert success
        assert base_model.model is not None
        assert base_model.tokenizer is not None
    finally:
        base_model.cleanup()
        gc.collect()

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
@patch("transformers.AutoModelForCausalLM.from_pretrained")
@patch("transformers.AutoTokenizer.from_pretrained")
def test_initialize_model_gpu(mock_tokenizer, mock_model, base_model):
    """Test model initialization on GPU."""
    mock_model.return_value = Mock()
    mock_tokenizer.return_value = Mock()
    mock_model.return_value.to.return_value = mock_model.return_value
    mock_model.return_value.parameters.return_value = iter([torch.tensor([1.0]).cuda()])
    
    try:
        success = base_model.initialize_model("deepseek-coder-small", use_gpu=True)
        assert success
        assert base_model.model is not None
        assert base_model.tokenizer is not None
        assert next(base_model.model.parameters()).device.type == "cuda"
    finally:
        base_model.cleanup()
        torch.cuda.empty_cache()
        gc.collect()

@patch("transformers.AutoModelForCausalLM.from_pretrained")
@patch("transformers.AutoTokenizer.from_pretrained")
def test_generate_text(mock_tokenizer, mock_model, base_model):
    """Test text generation."""
    mock_model.return_value = Mock()
    mock_tokenizer.return_value = Mock()
    mock_tokenizer.return_value.decode.return_value = "print('Hello, World!')"
    mock_model.return_value.generate.return_value = torch.tensor([[1, 2, 3]])
    
    try:
        base_model.initialize_model("deepseek-coder-small", use_gpu=False)
        prompt = "Write a hello world program in Python"
        response = base_model.generate(prompt)
        assert isinstance(response, str)
        assert len(response) > 0
    finally:
        base_model.cleanup()
        gc.collect()

def test_cleanup(base_model):
    """Test cleanup method."""
    with patch("transformers.AutoModelForCausalLM.from_pretrained") as mock_model, \
         patch("transformers.AutoTokenizer.from_pretrained") as mock_tokenizer:
        mock_model.return_value = Mock()
        mock_tokenizer.return_value = Mock()
        
        base_model.initialize_model("deepseek-coder-small", use_gpu=False)
        base_model.cleanup()
        assert base_model.model is None
        assert base_model.tokenizer is None
        gc.collect()

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
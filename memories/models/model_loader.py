"""Model loader for different providers."""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ModelLoader:
    """Loads and manages models from different providers."""
    
    SUPPORTED_PROVIDERS = {
        'openai',
        'anthropic',
        'deepseekai',  # Add support for deepseekai
        'local'
    }
    
    def __init__(self, provider: str, config: Optional[Dict[str, Any]] = None):
        """Initialize model loader.
        
        Args:
            provider: Model provider name
            config: Optional configuration dictionary
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
            
        self.provider = provider
        self.config = config or {}
        self.model = None
    
    def load_model(self) -> Any:
        """Load the model based on provider and config.
        
        Returns:
            Loaded model instance
        """
        try:
            if self.provider == 'deepseekai':
                # Import deepseekai module
                try:
                    import deepseek_ai
                    self.model = deepseek_ai.Model(**self.config)
                except ImportError:
                    raise ImportError("deepseekai package not installed")
            elif self.provider == 'openai':
                import openai
                self.model = openai.Model(**self.config)
            elif self.provider == 'anthropic':
                import anthropic
                self.model = anthropic.Model(**self.config)
            elif self.provider == 'local':
                from .local_model import LocalModel
                self.model = LocalModel(**self.config)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
            return self.model
            
        except Exception as e:
            logger.error(f"Error loading model from {self.provider}: {e}")
            raise
    
    def get_response(self, prompt: str, **kwargs) -> str:
        """Get response from the loaded model.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional arguments for the model
            
        Returns:
            Model response
        """
        if not self.model:
            self.load_model()
            
        try:
            if self.provider == 'deepseekai':
                return self.model.generate(prompt, **kwargs)
            elif self.provider == 'openai':
                return self.model.complete(prompt, **kwargs)
            elif self.provider == 'anthropic':
                return self.model.complete(prompt, **kwargs)
            elif self.provider == 'local':
                return self.model.generate(prompt, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error getting response from {self.provider}: {e}")
            raise
    
    def cleanup(self) -> None:
        """Clean up model resources."""
        if self.model and hasattr(self.model, 'cleanup'):
            try:
                self.model.cleanup()
            except Exception as e:
                logger.warning(f"Error during model cleanup: {e}")
        self.model = None 
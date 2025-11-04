"""
Model state manager for handling GPU model loading/unloading.
Replaces global state variables with proper dependency injection.
"""

import logging
from typing import List, Set, Optional, Any
from threading import Lock
import weakref

logger = logging.getLogger(__name__)

class ModelStateManager:
    """Manages model loading/unloading state in GPU memory."""
    
    _instance = None
    _lock = Lock()
    
    def __init__(self):
        """Initialize the model state manager."""
        self._models_in_gpu: Set[Any] = set()
        self._model_refs = weakref.WeakSet()
        self._instance_lock = Lock()
        
    @classmethod
    def get_instance(cls) -> 'ModelStateManager':
        """Get singleton instance with proper thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _torch_gc(self) -> None:
        """Garbage collection for PyTorch models."""
        try:
            import torch
            import gc
            
            with torch.no_grad():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            gc.collect()
        except ImportError:
            # PyTorch not available
            import gc
            gc.collect()
    
    def unload_models(self, models: List[Any]) -> None:
        """Unload specified models from GPU memory.
        
        Args:
            models: List of models to unload
        """
        with self._instance_lock:
            for model in models:
                if model in self._models_in_gpu:
                    try:
                        if hasattr(model, 'to'):
                            model.to('cpu')
                        logger.debug(f'Unloaded model to CPU: {model.__class__.__name__}')
                        self._models_in_gpu.discard(model)
                    except Exception as e:
                        logger.error(f"Error unloading model {model}: {e}")
            
            self._torch_gc()
    
    def load_models(self, models: List[Any], device: str = 'cuda') -> None:
        """Load specified models to GPU memory.
        
        Args:
            models: List of models to load
            device: Target device (default: 'cuda')
        """
        with self._instance_lock:
            for model in models:
                if model not in self._models_in_gpu:
                    try:
                        if hasattr(model, 'to'):
                            model.to(device)
                        logger.debug(f'Loaded model to {device}: {model.__class__.__name__}')
                        self._models_in_gpu.add(model)
                        self._model_refs.add(model)
                    except Exception as e:
                        logger.error(f"Error loading model {model}: {e}")
    
    def get_models_in_gpu(self) -> Set[Any]:
        """Get set of models currently in GPU memory.
        
        Returns:
            Set of models in GPU
        """
        with self._instance_lock:
            # Clean up dead references
            self._models_in_gpu = {m for m in self._models_in_gpu if m in self._model_refs}
            return self._models_in_gpu.copy()
    
    def manage_gpu_models(self, models: List[Any], device: str = 'cuda') -> None:
        """Manage GPU model loading with memory optimization.
        
        Args:
            models: List of models that should be in GPU
            device: Target device
        """
        with self._instance_lock:
            current_models = self.get_models_in_gpu()
            models_set = set(models)
            
            # Models to keep (intersection)
            models_to_remain = [m for m in models_set if m in current_models]
            
            # Models to load (not currently in GPU)
            models_to_load = [m for m in models_set if m not in current_models]
            
            # Models to unload (in GPU but not needed)
            models_to_unload = [m for m in current_models if m not in models_set]
            
            # Unload unnecessary models first
            if models_to_unload:
                self.unload_models(models_to_unload)
            
            # Load new models
            if models_to_load:
                self.load_models(models_to_load, device)
    
    def clear_all_models(self) -> None:
        """Clear all models from GPU memory."""
        with self._instance_lock:
            current_models = list(self._models_in_gpu)
            self.unload_models(current_models)
            self._models_in_gpu.clear()
    
    def __del__(self):
        """Cleanup when manager is destroyed."""
        try:
            self.clear_all_models()
        except Exception:
            pass

# Global instance accessor
def get_model_state_manager() -> ModelStateManager:
    """Get the global model state manager instance."""
    return ModelStateManager.get_instance()
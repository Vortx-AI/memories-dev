from .agent import Agent  # Explicitly export classes

"""
Base agent implementation for the memories system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from memories.models.load_model import LoadModel

class BaseAgent(ABC):
    """Base class for all agents in the memories system."""
    
    def __init__(self, memory_store: Any = None, name: str = "base_agent", model: Optional[LoadModel] = None):
        """Initialize the base agent.
        
        Args:
            memory_store: The memory store to use for this agent.
            name: Name identifier for the agent.
            model: Optional LoadModel instance for agents that need ML capabilities.
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(name)
        
        # Initialize components
        self.memory_store = memory_store
        self.name = name
        self.model = model
        
        # Initialize model if needed and not provided
        if model is None and self.requires_model():
            self.model = self._initialize_model()
    
    def requires_model(self) -> bool:
        """Override this method to indicate if the agent requires a model."""
        return False
    
    def _initialize_model(self) -> Optional[LoadModel]:
        """Initialize the model if required. Override this in child classes if needed."""
        if self.requires_model():
            return LoadModel(
                use_gpu=True,
                model_provider="deepseek-ai",
                deployment_type="deployment",
                model_name="deepseek-coder-1.3b-base"
            )
        return None
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Dict[str, Any]:
        """Process data using this agent.
        
        This method should be implemented by all concrete agent classes.
        Returns:
            Dict[str, Any]: Processing results with at least these keys:
                - status: "success" or "error"
                - data: The processed data (if successful)
                - error: Error message (if failed)
        """
        pass
    
    def cleanup(self):
        """Clean up any resources used by the agent."""
        if self.model:
            self.model.cleanup()
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name={self.name})"

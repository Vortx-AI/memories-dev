from .agent import Agent  # Explicitly export classes

"""
Base agent implementation for the memories system.
"""

from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    """Base class for all agents in the memories system."""
    
    def __init__(self, memory_store: Any):
        """Initialize the base agent.
        
        Args:
            memory_store: The memory store to use for this agent.
        """
        self.memory_store = memory_store
    
    @abstractmethod
    async def process(self, *args, **kwargs):
        """Process data using this agent.
        
        This method should be implemented by all concrete agent classes.
        """
        pass

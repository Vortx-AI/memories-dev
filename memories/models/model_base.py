"""
Base model implementation for the memories system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable, Set
import logging
from dataclasses import dataclass
from memories.models.load_model import LoadModel

@dataclass
class ModelState:
    """Represents the current state of a model."""
    status: str = "idle"  # idle, planning, executing, completed, error
    current_goal: Optional[str] = None
    current_plan: Optional[List[str]] = None
    memory: Dict[str, Any] = None
    last_action: Optional[str] = None
    last_result: Optional[Any] = None
    error: Optional[str] = None

class Tool:
    """Represents a tool that a model can use."""
    
    def __init__(self, name: str, func: Callable, description: str, required_args: Set[str]):
        """
        Initialize a tool.
        
        Args:
            name: Name of the tool
            func: The function to call when using the tool
            description: Description of what the tool does
            required_args: Set of required argument names
        """
        self.name = name
        self.func = func
        self.description = description
        self.required_args = required_args
    
    def can_handle(self, goal: str) -> bool:
        """Check if this tool can help achieve the given goal."""
        return any(keyword in goal.lower() for keyword in self.description.lower().split())
    
    def validate_args(self, **kwargs) -> bool:
        """Validate that all required arguments are provided."""
        return all(arg in kwargs for arg in self.required_args)
    
    def __call__(self, *args, **kwargs):
        """Execute the tool function."""
        if not self.validate_args(**kwargs):
            missing = self.required_args - set(kwargs.keys())
            raise ValueError(f"Missing required arguments: {missing}")
        return self.func(*args, **kwargs)

class BaseModel(ABC):
    """Base class for all models in the memories system."""
    
    def __init__(self, memory_store: Any = None, name: str = "base_model", model: Optional[LoadModel] = None):
        """Initialize the base model.
        
        Args:
            memory_store: The memory store to use for this model.
            name: Name identifier for the model.
            model: LoadModel instance for models that need ML capabilities.
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
        self.tools: Dict[str, Tool] = {}
        self.state = ModelState(memory={})
        
        # Validate model requirement
        if self.requires_model() and model is None:
            raise ValueError(f"Model {self.name} requires a model but none was provided")
        self.model = model
        
        # Initialize tools
        self._initialize_tools()
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return a list of high-level capabilities this model provides."""
        pass
    
    def can_handle_goal(self, goal: str) -> bool:
        """Check if this model can handle the given goal."""
        return any(tool.can_handle(goal) for tool in self.tools.values())
    
    def plan(self, goal: str) -> List[str]:
        """
        Create a plan to achieve the given goal.
        
        Args:
            goal: The goal to achieve
            
        Returns:
            List of tool names to execute in sequence
        """
        self.state.status = "planning"
        self.state.current_goal = goal
        
        # Simple planning: find tools that can handle the goal
        plan = []
        for name, tool in self.tools.items():
            if tool.can_handle(goal):
                plan.append(name)
        
        self.state.current_plan = plan
        return plan
    
    def execute_plan(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the current plan.
        
        Args:
            **kwargs: Arguments needed by the tools
            
        Returns:
            Dictionary containing execution results
        """
        if not self.state.current_plan:
            return {
                "status": "error",
                "error": "No plan to execute",
                "data": None
            }
        
        self.state.status = "executing"
        results = []
        
        try:
            for tool_name in self.state.current_plan:
                self.state.last_action = tool_name
                tool = self.tools[tool_name]
                
                # Execute the tool
                result = tool(**kwargs)
                results.append(result)
                
                # Update state
                self.state.last_result = result
                self.state.memory[tool_name] = result
            
            self.state.status = "completed"
            return {
                "status": "success",
                "data": results,
                "error": None
            }
            
        except Exception as e:
            self.state.status = "error"
            self.state.error = str(e)
            return {
                "status": "error",
                "error": str(e),
                "data": results
            }
    
    def requires_model(self) -> bool:
        """Override this method to indicate if the model requires a model."""
        return False
    
    def _initialize_tools(self):
        """Initialize the tools this model can use. Override in subclasses."""
        pass
    
    def register_tool(self, name: str, func: Callable, description: str, required_args: Set[str] = None):
        """
        Register a new tool for the model to use.
        
        Args:
            name: Name of the tool
            func: The function to call when using the tool
            description: Description of what the tool does
            required_args: Set of required argument names
        """
        self.tools[name] = Tool(name, func, description, required_args or set())
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """List all available tools."""
        return [{"name": name, "description": tool.description} 
                for name, tool in self.tools.items()]
    
    def use_tool(self, name: str, *args, **kwargs) -> Any:
        """
        Use a specific tool.
        
        Args:
            name: Name of the tool to use
            *args: Positional arguments for the tool
            **kwargs: Keyword arguments for the tool
            
        Returns:
            The result of the tool execution
        """
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
            
        self.state.last_action = name
        result = tool(*args, **kwargs)
        self.state.last_result = result
        self.state.memory[name] = result
        
        return result
    
    @abstractmethod
    async def process(self, goal: str, **kwargs) -> Dict[str, Any]:
        """
        Process a goal using this model.
        
        Args:
            goal: The goal to achieve
            **kwargs: Additional arguments needed by tools
            
        Returns:
            Dict containing processing results
        """
        pass
    
    def cleanup(self):
        """Clean up any resources used by the model."""
        if self.model:
            self.model.cleanup()
    
    def get_state(self) -> ModelState:
        """Get the current state of the model."""
        return self.state
    
    def reset_state(self):
        """Reset the model's state."""
        self.state = ModelState(memory={})
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(name={self.name}, status={self.state.status})" 
"""Function calling utilities for model integrations."""

import json
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """Parameter types for function definitions."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class Parameter:
    """Represents a function parameter."""
    name: str
    type: ParameterType
    description: str
    required: bool = False
    enum: Optional[List[Any]] = None
    items: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        param_dict = {
            "type": self.type.value,
            "description": self.description
        }

        if self.enum:
            param_dict["enum"] = self.enum

        if self.items:
            param_dict["items"] = self.items

        if self.properties:
            param_dict["properties"] = self.properties

        return param_dict


@dataclass
class FunctionDefinition:
    """Represents a function definition for model calling."""
    name: str
    description: str
    parameters: List[Parameter]
    function: Optional[Callable] = None

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function format.

        Returns:
            Dict in OpenAI function format
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_dict()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format.

        Returns:
            Dict in Anthropic tool format
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_dict()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    def execute(self, **kwargs) -> Any:
        """Execute the function with provided arguments.

        Args:
            **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            ValueError: If function is not set or required params missing
        """
        if not self.function:
            raise ValueError(f"Function {self.name} has no implementation")

        # Validate required parameters
        required_params = [p.name for p in self.parameters if p.required]
        missing = set(required_params) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        try:
            result = self.function(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Error executing function {self.name}: {str(e)}", exc_info=True)
            raise


class FunctionRegistry:
    """Registry for managing function definitions."""

    def __init__(self):
        """Initialize function registry."""
        self.functions: Dict[str, FunctionDefinition] = {}

    def register(self, function_def: FunctionDefinition):
        """Register a function.

        Args:
            function_def: Function definition to register
        """
        self.functions[function_def.name] = function_def
        logger.info(f"Registered function: {function_def.name}")

    def get(self, name: str) -> Optional[FunctionDefinition]:
        """Get a function by name.

        Args:
            name: Function name

        Returns:
            Function definition or None
        """
        return self.functions.get(name)

    def list_functions(self) -> List[str]:
        """List all registered function names.

        Returns:
            List of function names
        """
        return list(self.functions.keys())

    def to_openai_format(self) -> List[Dict[str, Any]]:
        """Get all functions in OpenAI format.

        Returns:
            List of functions in OpenAI format
        """
        return [f.to_openai_format() for f in self.functions.values()]

    def to_anthropic_format(self) -> List[Dict[str, Any]]:
        """Get all functions in Anthropic format.

        Returns:
            List of functions in Anthropic format
        """
        return [f.to_anthropic_format() for f in self.functions.values()]


class FunctionCallHandler:
    """Handles function call execution and result formatting."""

    def __init__(self, registry: FunctionRegistry):
        """Initialize function call handler.

        Args:
            registry: Function registry
        """
        self.registry = registry

    def execute_function_call(
        self,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a function call.

        Args:
            function_name: Name of function to call
            arguments: Function arguments

        Returns:
            Dict with execution result
        """
        function_def = self.registry.get(function_name)

        if not function_def:
            return {
                "success": False,
                "error": f"Function {function_name} not found",
                "result": None
            }

        try:
            result = function_def.execute(**arguments)
            return {
                "success": True,
                "error": None,
                "result": result
            }
        except Exception as e:
            logger.error(f"Function execution error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    def process_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        format: str = "openai"
    ) -> List[Dict[str, Any]]:
        """Process multiple tool calls.

        Args:
            tool_calls: List of tool calls from model
            format: Format of tool calls ("openai" or "anthropic")

        Returns:
            List of execution results
        """
        results = []

        for tool_call in tool_calls:
            if format == "openai":
                function_name = tool_call["function"]["name"]
                arguments_str = tool_call["function"]["arguments"]
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    results.append({
                        "success": False,
                        "error": "Invalid JSON arguments",
                        "result": None
                    })
                    continue
            elif format == "anthropic":
                function_name = tool_call["name"]
                arguments = tool_call["input"]
            else:
                results.append({
                    "success": False,
                    "error": f"Unsupported format: {format}",
                    "result": None
                })
                continue

            result = self.execute_function_call(function_name, arguments)
            results.append(result)

        return results


# Common function definitions
def create_weather_function() -> FunctionDefinition:
    """Create a weather query function definition.

    Returns:
        Weather function definition
    """
    return FunctionDefinition(
        name="get_weather",
        description="Get the current weather in a location",
        parameters=[
            Parameter(
                name="location",
                type=ParameterType.STRING,
                description="The city and state, e.g. San Francisco, CA",
                required=True
            ),
            Parameter(
                name="unit",
                type=ParameterType.STRING,
                description="The temperature unit to use",
                required=False,
                enum=["celsius", "fahrenheit"]
            )
        ]
    )


def create_search_function() -> FunctionDefinition:
    """Create a search function definition.

    Returns:
        Search function definition
    """
    return FunctionDefinition(
        name="search",
        description="Search for information on a given topic",
        parameters=[
            Parameter(
                name="query",
                type=ParameterType.STRING,
                description="The search query",
                required=True
            ),
            Parameter(
                name="max_results",
                type=ParameterType.INTEGER,
                description="Maximum number of results to return",
                required=False
            )
        ]
    )


def create_calculator_function() -> FunctionDefinition:
    """Create a calculator function definition.

    Returns:
        Calculator function definition
    """
    def calculate(operation: str, a: float, b: float) -> float:
        """Perform calculation."""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else None
        }
        return operations.get(operation, lambda x, y: None)(a, b)

    return FunctionDefinition(
        name="calculate",
        description="Perform mathematical calculations",
        parameters=[
            Parameter(
                name="operation",
                type=ParameterType.STRING,
                description="The operation to perform",
                required=True,
                enum=["add", "subtract", "multiply", "divide"]
            ),
            Parameter(
                name="a",
                type=ParameterType.NUMBER,
                description="First number",
                required=True
            ),
            Parameter(
                name="b",
                type=ParameterType.NUMBER,
                description="Second number",
                required=True
            )
        ],
        function=calculate
    )


def create_data_query_function() -> FunctionDefinition:
    """Create a data query function definition.

    Returns:
        Data query function definition
    """
    return FunctionDefinition(
        name="query_data",
        description="Query data from memory store",
        parameters=[
            Parameter(
                name="query",
                type=ParameterType.STRING,
                description="The query text",
                required=True
            ),
            Parameter(
                name="filters",
                type=ParameterType.OBJECT,
                description="Optional filters to apply",
                required=False,
                properties={
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string"},
                            "end": {"type": "string"}
                        }
                    },
                    "location": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lon": {"type": "number"},
                            "radius": {"type": "number"}
                        }
                    }
                }
            )
        ]
    )

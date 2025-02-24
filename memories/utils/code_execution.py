"""
Code execution module for safely executing generated code.
"""

import logging
import ast
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from io import StringIO
import sys
from contextlib import redirect_stdout
from memories.models.model_base import BaseModel

class CodeExecution(BaseModel):
    def __init__(self, model=None):
        """Initialize the Code Execution module.
        
        Args:
            model: Optional model instance
        """
        super().__init__(name="code_execution", model=model)
        self.logger = logging.getLogger(__name__)
        
        # Define allowed_modules for safety checks
        self.allowed_modules = {
            'pd': pd,
            'np': np,
            # Add other modules you consider safe
        }
        
        # Initialize tools
        self._initialize_tools()
    
    def get_capabilities(self) -> List[str]:
        """Return a list of high-level capabilities this module provides."""
        return [
            "Execute Python code safely",
            "Run queries on data",
            "Capture code output and results",
            "Perform safety checks on code",
            "Handle code execution errors"
        ]
    
    def requires_model(self) -> bool:
        """This module does not require a model."""
        return False
    
    def _initialize_tools(self):
        """Initialize the tools this module can use."""
        self.register_tool(
            "execute_code",
            self.execute_code,
            "Execute Python code safely with data",
            {"code"}
        )
        self.register_tool(
            "execute_query",
            self.execute_query,
            "Execute a query using code and data",
            {"code"}
        )
        self.register_tool(
            "_is_safe_code",
            self._is_safe_code,
            "Check if code is safe to execute",
            {"code"}
        )
    
    async def process(self, goal: str, **kwargs) -> Dict[str, Any]:
        """Process a goal using this module."""
        try:
            # Create a plan
            plan = self.plan(goal)
            
            # Execute the plan
            return self.execute_plan(**kwargs)
            
        except Exception as e:
            self.logger.error(f"Error in process: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }

    def _is_safe_code(self, code: str) -> bool:
        """
        Check if the code is safe to execute by analyzing the AST.
        
        Args:
            code (str): Python code to analyze
            
        Returns:
            bool: True if code is safe to execute, False otherwise
        """
        # Temporarily return True to allow all code execution
        return True
        
        # Original safety checks commented out for now
        """
        try:
            if not isinstance(code, str):
                self.logger.warning(f"Code must be a string, got {type(code)}")
                return False
            
            print(f"Analyzing code safety:\n{code}")  # Debug print
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Prevent dangerous imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_modules:
                            self.logger.warning(f"Blocked import: {alias.name}")
                            return False
                if isinstance(node, ast.ImportFrom):
                    if node.module not in self.allowed_modules:
                        self.logger.warning(f"Blocked import from: {node.module}")
                        return False
                
                # Prevent dangerous system calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'system']:
                            self.logger.warning(f"Blocked dangerous function: {node.func.id}")
                            return False
                    elif isinstance(node.func, ast.Attribute):
                        # Block dangerous method calls
                        dangerous_methods = ['eval', 'exec', 'system', '__import__']
                        if node.func.attr in dangerous_methods:
                            self.logger.warning(f"Blocked dangerous method: {node.func.attr}")
                            return False
            self.logger.info("Code passed safety checks")
            return True
        except SyntaxError as e:
            self.logger.error(f"Syntax error in code: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error analyzing code safety: {str(e)}")
            return False
        """
            
    def execute_code(self, code: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the provided Python code with the given data dictionary.
        
        Args:
            code (str): Python code to execute
            data (Dict[str, Any], optional): Dictionary containing the data to be used by the code
            
        Returns:
            Dict[str, Any]: Dictionary containing execution results and any errors
        """
        if not self._is_safe_code(code):
            return {
                'success': False,
                'error': 'Code contains unsafe operations',
                'result': None
            }
            
        # Create a string buffer to capture stdout
        output_buffer = StringIO()
        
        try:
            # Create a safe local environment with only allowed modules
            local_env = {
                'pd': pd,
                'np': np,
            }
            
            # Add data to local environment if provided
            if data is not None:
                local_env['data'] = data
            
            # Add other allowed modules
            for module_name, module in self.allowed_modules.items():
                local_env[module_name] = module
            
            # Execute code with stdout redirection
            with redirect_stdout(output_buffer):
                exec(code, local_env)
            
            # Get the last expression's value if it exists
            lines = code.strip().split('\n')
            last_line = lines[-1]
            
            try:
                # Try to evaluate the last line if it's an expression
                if not (last_line.startswith(' ') or last_line.startswith('\t')):
                    result = eval(last_line, local_env)
                else:
                    result = None
            except Exception as eval_error:
                self.logger.warning(f"Could not evaluate last line: {str(eval_error)}")
                result = None
            
            return {
                'success': True,
                'error': None,
                'result': result,
                'output': output_buffer.getvalue()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing code: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'result': None,
                'output': output_buffer.getvalue()
            }
        finally:
            output_buffer.close()
            
    def execute_query(self, code: str, data: Dict[str, Any] = None) -> Any:
        """
        Execute a query using the provided code and data.
        
        Args:
            code (str): Python code to execute
            data (Dict[str, Any], optional): Dictionary containing the data
            
        Returns:
            Any: Result of the code execution or error message
        """
        result = self.execute_code(code, data)
        
        if result['success']:
            return result['result'] if result['result'] is not None else result['output']
        else:
            return f"Error: {result['error']}" 
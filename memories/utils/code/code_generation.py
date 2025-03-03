"""
Code generation module for handling code generation and analysis.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from dotenv import load_dotenv
import tempfile
import json
from pathlib import Path
import duckdb
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from memories.models.api_connector import get_connector
from memories.models.model_base import BaseModel

# Load environment variables
load_dotenv()

class CodeGeneration(BaseModel):
    def __init__(self, model=None, offload_folder: Optional[str] = None):
        """Initialize the Code Generation module.
        
        Args:
            model: Optional model instance
            offload_folder: Optional folder for offloading data
        """
        super().__init__(name="code_generation", model=model)
        self.logger = logging.getLogger(__name__)
        
        # Load API knowledge base
        knowledge_path = os.path.join(os.getenv('PROJECT_ROOT', '.'), 'memories', 'utils', 'knowledge-base.json')
        try:
            with open(knowledge_path, 'r') as f:
                self.knowledge_base = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {str(e)}")
            raise
        
        # Initialize the Deepseek connector if no model provided
        self.llm = model or get_connector("deepseek", os.getenv("DEEPSEEK_API_KEY"))
        
        # Update prompt to instruct the LLM to generate code that calls the provided APIs.
        self.code_prompt = PromptTemplate(
            input_variables=["user_query", "knowledge_base"],
            template="""#Generate Python code to answer the following query using the provided API documentation.

#Query: {user_query}

#APIs and their details:
{knowledge_base}

#Your code should:
#1. Choose the most appropriate API based on the query.
#2. Construct proper HTTP requests using the API endpoints, methods, and parameters.
#3. Include necessary error handling and required imports.
#4. Follow best practices for Python coding.
#MUST not contain any text other than the code.Should not contain any comments or examples or expected outputs

#Generate only the Python code, with no additional explanation."""
        )
        
        self.code_chain = LLMChain(llm=self.llm, prompt=self.code_prompt)
        
        # Register tools
        self._initialize_tools()
    
    def get_capabilities(self) -> List[str]:
        """Return a list of high-level capabilities this module provides."""
        return [
            "Generate Python code from natural language queries",
            "Process queries using API documentation",
            "Extract and use knowledge base functions",
            "Clean and format generated code",
            "Analyze spatial queries and recommend functions"
        ]
    
    def requires_model(self) -> bool:
        """This module requires a model for code generation."""
        return True
    
    def _initialize_tools(self):
        """Initialize the tools this module can use."""
        self.register_tool(
            "process_query",
            self.process_query,
            "Process a natural language query and generate code",
            {"query"}
        )
        self.register_tool(
            "generate_code",
            self.generate_code,
            "Generate code based on a query",
            {"query"}
        )
        self.register_tool(
            "clean_generated_code",
            self.clean_generated_code,
            "Clean up generated code by removing formatting",
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

    def process_query(self, query: str, memories: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """Process a natural language query and generate appropriate code."""
        try:
            # Format API knowledge for the prompt
            knowledge_str = json.dumps({
                "apis": self.knowledge_base.get("apis", []),
                "metadata": self.knowledge_base.get("metadata", {}),
                "memories": memories
            }, indent=2)
            
            # Generate code using the updated prompt
            response = self.code_chain.invoke({
                "user_query": query,
                "knowledge_base": knowledge_str
            })
            
            generated_code = response["text"].strip()
            
            return generated_code, {"status": "success"}
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return f"# Error: {str(e)}", {"error": str(e)}

    def _extract_used_functions(self, code: str) -> list:
        """Extract the names of knowledge base functions used in the generated code."""
        functions = []
        for func_name in self.knowledge_base["landuse"]["python_functions"].keys():
            if func_name in code:
                functions.append(func_name)
        return functions

    def generate_code(self, query: str) -> str:
        """Generate code based on the query (legacy method for compatibility)."""
        code, _ = self.process_query(query)
        return code

    def clean_generated_code(self, code: str) -> str:
        """Clean up the generated code by removing markdown formatting and comments."""
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        code = code.strip()
        
        if "import" in code:
            code_lines = code.split('\n')
            for i, line in enumerate(code_lines):
                if 'import' in line:
                    code = '\n'.join(code_lines[i:])
                    break
        
        return code

class ModelAnalyst:
    def __init__(self, load_model: Any):
        """
        Initialize Model Analyst.

        Args:
            load_model: An LLM instance or similar component used for generating code.
        """
        self.load_model = load_model
        self.project_root = os.getenv("PROJECT_ROOT", "")

    def clean_generated_code(self, code: str) -> str:
        """
        Clean up the generated code by removing markdown formatting and comments.
        """
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        code = code.strip()
        
        if "import" in code:
            code_lines = code.split('\n')
            for i, line in enumerate(code_lines):
                if 'import' in line:
                    code = '\n'.join(code_lines[i:])
                    break
        
        return code

    def analyze_query(
        self,
        query: str,
        geometry: str,
        geometry_type: str,
        data_type: str,
        parquet_file: str,
        relevant_column: str,
        geometry_column: str = None,
        extra_params: Dict = None
    ) -> Dict[str, Any]:
        """
        Analyze a query and generate appropriate code for spatial analysis.
        
        Args:
            query: User's query
            geometry: Geometry string
            geometry_type: Type of geometry
            data_type: Type of data
            parquet_file: Path to parquet file
            relevant_column: Column to analyze
            geometry_column: Optional geometry column
            extra_params: Additional parameters
            
        Returns:
            Dict containing generated code and analysis
        """
        try:
            # Format the prompt
            prompt = f"""Generate Python code to analyze spatial data based on:
Query: {query}
Geometry: {geometry}
Type: {geometry_type}
Data: {data_type}
File: {parquet_file}
Column: {relevant_column}
"""
            if geometry_column:
                prompt += f"Geometry Column: {geometry_column}\n"
            if extra_params:
                prompt += f"Extra Parameters: {json.dumps(extra_params)}\n"
                
            # Generate code
            code = self.clean_generated_code(self.load_model.generate(prompt))
            
            return {
                "status": "success",
                "code": code,
                "analysis": {
                    "query_type": "spatial",
                    "geometry_type": geometry_type,
                    "data_type": data_type
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "code": None,
                "analysis": None
            } 
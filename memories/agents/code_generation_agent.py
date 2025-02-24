"""
Code generation agent for handling code generation and analysis.
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
from memories.agents.agent_base import BaseAgent

# Load environment variables
load_dotenv()

class CodeGenerationAgent(BaseAgent):
    def __init__(self, model=None, offload_folder: Optional[str] = None):
        """Initialize the Code Generation Agent.
        
        Args:
            model: Optional model instance
            offload_folder: Optional folder for offloading data
        """
        super().__init__(name="code_generation_agent", model=model)
        self.logger = logging.getLogger(__name__)
        
        # Load API knowledge base
        knowledge_path = os.path.join(os.getenv('PROJECT_ROOT', '.'), 'memories', 'agents', 'knowledge-base.json')
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
        """Return a list of high-level capabilities this agent provides."""
        return [
            "Generate Python code from natural language queries",
            "Process queries using API documentation",
            "Extract and use knowledge base functions",
            "Clean and format generated code",
            "Analyze spatial queries and recommend functions"
        ]
    
    def requires_model(self) -> bool:
        """This agent requires a model for code generation."""
        return True
    
    def _initialize_tools(self):
        """Initialize the tools this agent can use."""
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
        """Process a goal using this agent."""
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

class LocationExtractor:
    def __init__(self):
        """Initialize the Information Extraction system with NLTK."""
        offload_folder = os.path.join(
            tempfile.gettempdir(),
            'deepseek_offload'
        )
        os.makedirs(offload_folder, exist_ok=True)
        
        self.llm = get_connector("deepseek", os.getenv("DEEPSEEK_API_KEY"))
        
        self.location_prompt = PromptTemplate(
            input_variables=["user_query"],
            template="""Extract location information as a text string in the following format:
location: <place>, location_info: <type>

Types:
point = coordinates (12.345, 67.890)
city = city name
state = state name
country = country name
address = full address
polygon = area coordinates
unknown = no location found (use empty string)

Query: {user_query}
Response:"""
        )
        
        self.location_chain = LLMChain(llm=self.llm, prompt=self.location_prompt)
        self.logger = logging.getLogger(__name__)

    def process_query(self, user_query: str) -> str:
        """Process the query to extract location and information type."""
        try:
            location_response = self.location_chain.invoke({"user_query": user_query})["text"]
            return location_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return "location: , location_info: unknown"
            

class AgentAnalyst:
    def __init__(self, load_model: Any):
        """
        Initialize Agent Analyst.

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
        Analyze the query and recommend appropriate functions with parameters.
        """
        try:
            prompt = f"""
Given a spatial query and data details, recommend appropriate query functions with parameters.

Query: {query}
Data Type: {data_type}
Geometry: {geometry}
Geometry Type: {geometry_type}
Parquet File: {parquet_file}
Relevant Column: {relevant_column}
Geometry Column: {geometry_column if geometry_column else 'geometry'}

Available functions:
1. nearest_query - Find nearest records (default limit: 5)
2. within_area_query - Find records within the specified geometry
3. count_within_area_query - Count records within the specified geometry
4. exact_match_query - Find exact matches with spatial filtering

Return recommendations in this JSON format:
{{
    "status": "success",
    "recommendations": [
        {{
            "function_name": "function_name",
            "parameters": {{
                "parquet_file": "file_path",
                "column_name": "column_name",
                "value": "true/false",
                "geometry": "WKT_string",
                "geometry_type": "POINT/LINESTRING/POLYGON",
                "limit": number         // for nearest query
            }},
            "reason": "explanation"
        }}
    ]
}}

Note: All filter columns are boolean type, so value should be 'true' or 'false'.
"""
            # Get response from model
            response = self.load_model.get_response(prompt)
            
            # Parse the response
            try:
                if isinstance(response, str):
                    if "```json" in response:
                        response = response.split("```json")[1].split("```")[0]
                    elif "```" in response:
                        response = response.split("```")[1].split("```")[0]
                    
                    result = json.loads(response.strip())
                    
                    # Set default values for limit if it's a string
                    for rec in result.get('recommendations', []):
                        params = rec.get('parameters', {})
                        if 'limit' in params and not isinstance(params['limit'], (int, float)):
                            params['limit'] = 5   # Default 5 results
                        # Ensure value is boolean string
                        if 'value' in params:
                            params['value'] = 'true'  # Default to true for boolean columns
                        # Ensure geometry and geometry_type are set
                        if 'geometry' not in params:
                            params['geometry'] = geometry
                        if 'geometry_type' not in params:
                            params['geometry_type'] = geometry_type
                    
                    return result
                    
            except json.JSONDecodeError as e:
                return {
                    'status': 'error',
                    'error': f'Failed to parse response: {str(e)}',
                    'response': response
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
        
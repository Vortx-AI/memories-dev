"""
Overture Maps query handler with chat completion support.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import duckdb
from memories.models.load_model import LoadModel
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.data_acquisition.sources.overture_local import OvertureLocal

logger = logging.getLogger(__name__)

class OvertureQueryHandler:
    """Handles natural language queries for Overture Maps data."""
    
    def __init__(
        self,
        model: LoadModel,
        data_dir: Optional[str] = None,
        use_local: bool = True
    ):
        """Initialize the query handler.
        
        Args:
            model: LoadModel instance for chat completion
            data_dir: Directory for storing Overture data
            use_local: Whether to use local data (True) or API (False)
        """
        self.model = model
        self.data_dir = Path(data_dir) if data_dir else Path("data/overture")
        
        # Initialize Overture data source
        if use_local:
            self.overture = OvertureLocal(data_dir=str(self.data_dir))
        else:
            self.overture = OvertureAPI(data_dir=str(self.data_dir))
            
        # Initialize DuckDB connection
        self.con = duckdb.connect(database=":memory:")
        self.con.execute("INSTALL spatial;")
        self.con.execute("LOAD spatial;")
        
        # Define tools for the model
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_overture_data",
                    "description": "Query Overture Maps data using SQL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {
                                "type": "string",
                                "description": "SQL query to execute on Overture data"
                            },
                            "theme": {
                                "type": "string",
                                "description": "Overture theme to query (buildings, places, transportation, etc.)",
                                "enum": ["buildings", "places", "transportation", "base", "divisions", "addresses"]
                            }
                        },
                        "required": ["sql_query", "theme"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "spatial_search",
                    "description": "Search for features within a geographic area",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "bbox": {
                                "type": "object",
                                "properties": {
                                    "xmin": {"type": "number"},
                                    "ymin": {"type": "number"},
                                    "xmax": {"type": "number"},
                                    "ymax": {"type": "number"}
                                },
                                "required": ["xmin", "ymin", "xmax", "ymax"]
                            },
                            "themes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of themes to search"
                            }
                        },
                        "required": ["bbox", "themes"]
                    }
                }
            }
        ]
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query about Overture data.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary containing the response and any relevant data
        """
        try:
            # Prepare messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": """You are an AI assistant that helps users query Overture Maps data.
                    You can use SQL queries to extract information from the data, which includes:
                    - buildings: Information about buildings and structures
                    - places: Points of interest and named places
                    - transportation: Roads, railways, and other transportation features
                    - base: Basic geographic features like water bodies and land use
                    - divisions: Administrative boundaries
                    - addresses: Street addresses and locations
                    
                    When writing SQL queries:
                    1. Use appropriate spatial functions (ST_Intersects, ST_Distance, etc.)
                    2. Consider performance by adding appropriate filters
                    3. Handle NULL values appropriately
                    4. Use clear column aliases for readability
                    """
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            # Get chat completion with tools
            response = self.model.chat_completion(
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            # Process tool calls if any
            if response.get("tool_calls"):
                results = []
                for tool_call in response["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    args = tool_call["function"]["arguments"]
                    
                    if func_name == "query_overture_data":
                        result = await self._execute_query(args["sql_query"], args["theme"])
                        results.append(result)
                    elif func_name == "spatial_search":
                        result = await self.overture.search(args["bbox"])
                        results.append(result)
                        
                # Add results to conversation
                messages.append({
                    "role": "assistant",
                    "content": response["message"]["content"],
                    "tool_calls": response["tool_calls"]
                })
                messages.append({
                    "role": "system",
                    "content": f"Tool call results: {results}"
                })
                
                # Get final response interpreting the results
                final_response = self.model.chat_completion(
                    messages=messages,
                    temperature=0.7
                )
                
                return {
                    "query": query,
                    "response": final_response["message"]["content"],
                    "data": results
                }
            
            return {
                "query": query,
                "response": response["message"]["content"],
                "data": None
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "query": query,
                "response": f"Error processing query: {str(e)}",
                "data": None
            }
            
    async def _execute_query(self, sql_query: str, theme: str) -> Dict[str, Any]:
        """Execute a SQL query on Overture data.
        
        Args:
            sql_query: SQL query to execute
            theme: Overture theme to query
            
        Returns:
            Query results
        """
        try:
            # Get theme directory
            theme_dir = self.data_dir / theme
            if not theme_dir.exists():
                raise ValueError(f"No data found for theme: {theme}")
                
            # Find parquet files
            parquet_files = list(theme_dir.glob("**/*.parquet"))
            if not parquet_files:
                raise ValueError(f"No parquet files found for theme: {theme}")
                
            # Create view of all parquet files
            files_str = ",".join(f"'{str(f)}'" for f in parquet_files)
            view_query = f"""
            CREATE OR REPLACE VIEW {theme}_view AS 
            SELECT * FROM read_parquet([{files_str}])
            """
            self.con.execute(view_query)
            
            # Execute query
            if "from" not in sql_query.lower():
                sql_query = f"{sql_query} FROM {theme}_view"
                
            result = self.con.execute(sql_query).fetchdf()
            
            return {
                "theme": theme,
                "query": sql_query,
                "result": result.to_dict("records"),
                "row_count": len(result)
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
            
    def cleanup(self):
        """Clean up resources."""
        if self.con:
            self.con.close()
        if hasattr(self, "overture"):
            del self.overture 
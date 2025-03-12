"""
Memory Chat Standalone Example with DuckDB Integration

This module provides a simple interface to interact with AI models
for chat completion functionality with DuckDB integration for Dubai OSM data.
"""

import os
import json
import logging
import requests
import threading
import time
import queue
from typing import Dict, Any, List, Optional, Tuple, Union
import duckdb
from pathlib import Path
from dotenv import load_dotenv

# Import LoadModel from memories package
from memories.models.load_model import LoadModel

# Load environment variables from .env file
load_dotenv()

# Create logs directory in user's home directory
log_dir = os.path.expanduser("~/memories_logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "memory_chat.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

class MemoryChat:
    """
    A class to interact with AI models for chat completion with DuckDB integration.
    """
    
    def __init__(
        self,
        endpoint: str = os.getenv("MODEL_ENDPOINT"),
        api_key: str = os.getenv("MODEL_API_KEY"),
        model_name: str = os.getenv("MODEL_NAME", "gpt-4"),
        model_provider: str = os.getenv("MODEL_PROVIDER", "openai"),
        deployment_type: str = os.getenv("MODEL_DEPLOYMENT_TYPE", "api"),
        duckdb_path: str = "/home/jaya/dubai_osm.duckdb",
        duckdb_timeout: int = 10  # Timeout for DuckDB queries in seconds
    ):
        """
        Initialize the MemoryChat with model configuration and DuckDB.
        
        Args:
            endpoint (str): The model endpoint URL
            api_key (str): The API key for authentication
            model_name (str): The name of the model to use
            model_provider (str): The model provider (e.g., "openai", "azure-ai")
            deployment_type (str): Type of deployment (e.g., "api")
            duckdb_path (str): Path to the DuckDB database for L1_2 queries
            duckdb_timeout (int): Timeout for DuckDB queries in seconds
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.model_name = model_name
        self.model_provider = model_provider
        self.deployment_type = deployment_type
        self.duckdb_path = duckdb_path
        self.duckdb_con = None
        self.duckdb_timeout = duckdb_timeout
        
        # Queue to store pending DuckDB query results
        self.query_results_queue = queue.Queue()
        
        # Track active DuckDB queries
        self.active_queries = {}
        
        # Print environment variables for debugging (without showing full API key)
        env_vars = {
            "MODEL_ENDPOINT": os.getenv("MODEL_ENDPOINT", "Not set"),
            "MODEL_API_KEY": "****" + (os.getenv("MODEL_API_KEY", "")[-4:] if os.getenv("MODEL_API_KEY") else "Not set"),
            "MODEL_NAME": os.getenv("MODEL_NAME", "Not set"),
            "MODEL_PROVIDER": os.getenv("MODEL_PROVIDER", "Not set"),
            "MODEL_DEPLOYMENT_TYPE": os.getenv("MODEL_DEPLOYMENT_TYPE", "Not set")
        }
        logger.info(f"Environment variables: {env_vars}")
        
        # Validate required configuration
        if not self.api_key:
            error_msg = "Missing required API key. Please check your .env file and ensure MODEL_API_KEY is set."
            logger.error(error_msg)
            print("\nERROR: " + error_msg)
            print("Current working directory:", os.getcwd())
            print("Looking for .env file in:", os.path.join(os.getcwd(), ".env"))
            if os.path.exists(os.path.join(os.getcwd(), ".env")):
                print(".env file exists. Please check its contents.")
                with open(os.path.join(os.getcwd(), ".env"), 'r') as f:
                    env_content = f.read()
                    print("First few characters of .env file:", env_content[:50] + "..." if len(env_content) > 50 else env_content)
            else:
                print(".env file not found. Please create one with MODEL_API_KEY=your_api_key")
            raise ValueError(error_msg)
        
        # Initialize LoadModel
        try:
            self.model = LoadModel(
                model_provider=model_provider,
                deployment_type=deployment_type,
                model_name=model_name,
                api_key=api_key,
                endpoint=endpoint
            )
            logger.info(f"Successfully initialized LoadModel with {model_name} at {endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize LoadModel: {e}")
            raise
        
        # Initialize DuckDB connection
        self._init_duckdb()
    
    def _init_duckdb(self):
        """Initialize connection to DuckDB database."""
        try:
            if os.path.exists(self.duckdb_path):
                self.duckdb_con = duckdb.connect(self.duckdb_path, read_only=True)
                logger.info(f"Successfully connected to DuckDB at {self.duckdb_path}")
                
                # Install and load the spatial extension required for geographic queries
                try:
                    self.duckdb_con.execute("INSTALL spatial;")
                    self.duckdb_con.execute("LOAD spatial;")
                    logger.info("Successfully installed and loaded the spatial extension")
                except Exception as e:
                    logger.error(f"Failed to load spatial extension: {e}")
                    print(f"Error: Unable to load spatial extension. Geographic queries will not work properly.")
                    print(f"Error details: {e}")
                
                # Get available tables
                tables = self.duckdb_con.execute("SHOW TABLES").fetchall()
                table_names = [table[0] for table in tables]
                logger.info(f"Available tables in DuckDB: {table_names}")
                
                if not table_names:
                    logger.warning(f"No tables found in DuckDB at {self.duckdb_path}")
                    print(f"Warning: DuckDB database exists but contains no tables.")
            else:
                logger.warning(f"DuckDB file not found at {self.duckdb_path}")
                print(f"Warning: DuckDB file not found at {self.duckdb_path}")
                print(f"L1_2 queries requiring geographic data will not work properly.")
                print(f"Please ensure the file exists and is accessible.")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            print(f"Error connecting to DuckDB: {e}")
            self.duckdb_con = None
    
    def query_duckdb(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query on the DuckDB database.
        
        Args:
            sql_query (str): SQL query to execute
            
        Returns:
            Dict containing query results or error message
        """
        try:
            if not self.duckdb_con:
                self._init_duckdb()
                
            if not self.duckdb_con:
                return {"error": f"Could not connect to DuckDB at {self.duckdb_path}"}
                
            # Execute query and convert to pandas DataFrame
            result = self.duckdb_con.execute(sql_query).fetchdf()
            
            # Convert to dictionary for JSON serialization
            return {
                "success": True,
                "data": result.to_dict(orient="records"),
                "columns": result.columns.tolist(),
                "row_count": len(result)
            }
        except Exception as e:
            logger.error(f"Error executing DuckDB query: {e}")
            return {"error": str(e)}
    
    def async_query_duckdb(self, query_id: str, sql_query: str, user_query: str) -> None:
        """
        Execute a DuckDB query asynchronously and put the result in the queue.
        
        Args:
            query_id (str): Unique identifier for the query
            sql_query (str): SQL query to execute
            user_query (str): Original user question
        """
        try:
            logger.info(f"Starting async DuckDB query with ID {query_id}")
            logger.info(f"Executing SQL: {sql_query}")
            
            # Execute query
            query_result = self.query_duckdb(sql_query)
            
            # Log the result status
            if "error" in query_result:
                logger.error(f"DuckDB query error: {query_result['error']}")
            else:
                row_count = query_result.get('row_count', 0)
                logger.info(f"DuckDB query successful, retrieved {row_count} rows")
            
            # Add result to queue with query ID
            self.query_results_queue.put({
                "query_id": query_id,
                "user_query": user_query,
                "sql_query": sql_query,
                "result": query_result,
                "timestamp": time.time()
            })
            
            logger.info(f"Completed async DuckDB query with ID {query_id}")
            
            # Remove from active queries
            if query_id in self.active_queries:
                del self.active_queries[query_id]
                
        except Exception as e:
            logger.error(f"Error in async_query_duckdb: {e}")
            self.query_results_queue.put({
                "query_id": query_id,
                "user_query": user_query,
                "sql_query": sql_query,
                "result": {"error": str(e)},
                "timestamp": time.time()
            })
            
            # Remove from active queries
            if query_id in self.active_queries:
                del self.active_queries[query_id]
    
    def get_response_with_data(
        self, 
        messages: List[Dict[str, str]], 
        data_context: str, 
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate a response with geographic data from DuckDB.
        
        Args:
            messages (List[Dict[str, str]]): List of message objects
            data_context (str): Context with geographic data
            temperature (float): Temperature for response generation
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            Dict[str, Any]: The model's response
        """
        # Create a copy of messages to avoid modifying the original
        data_messages = messages.copy()
        
        # Add data context to system message
        system_message_found = False
        for i, msg in enumerate(data_messages):
            if msg["role"] == "system":
                system_message_found = True
                data_messages[i]["content"] += "\n\n" + data_context
                break
        
        # If no system message, add one
        if not system_message_found:
            data_messages.insert(0, {
                "role": "system",
                "content": f"You are a helpful assistant with access to geographic data. {data_context}"
            })
            
        # Add instruction to use the geographic data
        data_messages.append({
            "role": "system",
            "content": """Please provide an improved response based on the Dubai geographic data 
            that has been added to your context. This is a follow-up to your previous response,
            so focus on providing new insights based on the data."""
        })
        
        try:
            # Get response with data
            response = self.model.chat_completion(
                messages=data_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Standardize response format
            standardized_response = {"message": {}}
            
            if isinstance(response, dict):
                if "message" in response:
                    message = response["message"]
                    if isinstance(message, dict) and "content" in message:
                        standardized_response["message"]["content"] = message["content"]
                    elif isinstance(message, str):
                        standardized_response["message"]["content"] = message
                    else:
                        standardized_response["message"]["content"] = str(message)
                elif "choices" in response and len(response["choices"]) > 0:
                    # OpenAI format
                    choice = response["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        standardized_response["message"]["content"] = choice["message"]["content"]
                    else:
                        standardized_response["message"]["content"] = str(choice)
                else:
                    standardized_response["message"]["content"] = str(response)
            elif isinstance(response, str):
                # Handle string response directly
                standardized_response["message"]["content"] = response
            else:
                standardized_response["message"]["content"] = str(response)
            
            # Add metadata if available
            if isinstance(response, dict) and "metadata" in response:
                standardized_response["metadata"] = response["metadata"]
            elif isinstance(response, dict) and "usage" in response:
                standardized_response["metadata"] = {"total_tokens": response["usage"].get("total_tokens", 0)}
            
            return standardized_response
        except Exception as e:
            logger.error(f"Error generating response with data: {e}")
            return {"error": str(e)}
    
    def start_async_duckdb_query(self, user_query: str, messages: List[Dict[str, str]]) -> str:
        """
        Start an asynchronous DuckDB query process for L1_2 queries.
        
        Args:
            user_query (str): User's query
            messages (List[Dict[str, str]]): Current conversation messages
            
        Returns:
            str: Query ID if query started, None otherwise
        """
        try:
            if not self.duckdb_con:
                logger.warning("DuckDB not connected, skipping async query")
                return None
                
            # Check for forced L1_2 classification
            if user_query.startswith("[FORCE_L1_2]"):
                logger.info("Forced L1_2 classification detected")
                user_query = user_query.replace("[FORCE_L1_2]", "").strip()
                is_l1_2 = True
            else:
                # Direct keyword detection for obvious geographic queries
                # This serves as a fallback if the classification fails
                dubai_geo_keywords = [
                    "burj khalifa", "dubai mall", "palm jumeirah", "dubai marina", "business bay",
                    "downtown dubai", "deira", "jumeirah", "sheikh zayed", "properties in dubai",
                    "buildings in dubai", "restaurants in dubai", "hotels in dubai", "parks in dubai",
                    "schools in dubai", "hospitals in dubai", "roads in dubai", "bounding box",
                    "nearest to", "closest to", "within", "radius", "distance from", "facing"
                ]
                
                lower_query = user_query.lower()
                is_l1_2 = False
                
                # Check if any Dubai geographic keyword is in the query
                for keyword in dubai_geo_keywords:
                    if keyword in lower_query:
                        is_l1_2 = True
                        logger.info(f"Direct keyword match '{keyword}' detected in query, likely L1_2 query")
                        break
                        
                # Additional detection for queries asking about counts with location components
                if not is_l1_2 and any(word in lower_query for word in ["how many", "count", "number of", "find", "list", "top"]) and \
                   any(word in lower_query for word in ["dubai", "burj", "jumeirah", "properties", "buildings", "roads"]):
                    is_l1_2 = True
                    logger.info(f"Count/list query with location component detected, likely L1_2 query")
                
                # Detect complex spatial queries
                if not is_l1_2 and any(phrase in lower_query for phrase in ["north side", "south side", "east side", "west side", 
                                                                         "adjacent to", "next to", "facing", "near"]):
                    is_l1_2 = True
                    logger.info(f"Spatial relationship query detected, likely L1_2 query")
                
                # Detect "top N" recommendation patterns
                if not is_l1_2 and any(pattern in lower_query for pattern in ["top 5", "top five", "5 best", "5 most", "recommend", "recommendation"]):
                    is_l1_2 = True
                    logger.info(f"Recommendation query detected, likely L1_2 query")
                
                # If not directly detected, use model classification
                if not is_l1_2:
                    # Check if this is an L1_2 query using a simple classification
                    classification_messages = [
                        {"role": "system", "content": """Analyze the following query and classify it into one of these categories:
                        N: Query has NO location component and can be answered by any AI model
                        L0: Query HAS location component but can still be answered without additional data
                        L1_2: Query HAS location component and NEEDS additional geographic data
                        
                        Examples of L1_2 queries:
                        "How many restaurants are there in Dubai?"
                        "Find properties near Burj Khalifa"
                        "Buildings with roads on the north side"
                        "List top 5 properties with their bounding boxes"
                        "Show me properties near Burj Khalifa with a road on the north side"
                        "I want to buy a property near Burj Khalifa with a road on the north side"
                        
                        Return ONLY the classification label (N, L0, or L1_2) without any explanation or additional text."""},
                        {"role": "user", "content": user_query}
                    ]
                    
                    # Get classification
                    classification_response = self.model.chat_completion(
                        messages=classification_messages,
                        temperature=0.0,
                        max_tokens=10
                    )
                    
                    # Extract classification
                    classification = None
                    if isinstance(classification_response, dict):
                        # Handle dictionary response
                        if "message" in classification_response:
                            message = classification_response["message"]
                            if isinstance(message, dict) and "content" in message:
                                content = message["content"]
                            elif isinstance(message, str):
                                content = message
                            else:
                                content = str(message)
                        elif "choices" in classification_response and len(classification_response["choices"]) > 0:
                            # OpenAI format
                            choice = classification_response["choices"][0]
                            if "message" in choice and "content" in choice["message"]:
                                content = choice["message"]["content"]
                            else:
                                content = str(choice)
                        else:
                            content = str(classification_response)
                    elif isinstance(classification_response, str):
                        # Handle string response directly
                        content = classification_response
                    else:
                        content = str(classification_response)
                    
                    # Extract classification from the content - handle different formats
                    content = content.strip()
                    logger.info(f"Raw classification response: {content}")
                    
                    # Check if content contains L1_2 in various formats
                    # Look for direct match
                    if "L1_2" in content:
                        is_l1_2 = True
                    # Look for classification formatting
                    elif "Classification:" in content and "L1_2" in content:
                        is_l1_2 = True
                    # Look for other variations
                    elif "L1-2" in content or "L1.2" in content or "L12" in content:
                        is_l1_2 = True
                    # Look for key phrases indicating geographic data need
                    elif any(phrase in content.lower() for phrase in ["needs geographic data", "requires geographic data", 
                                                                   "needs location data", "requires spatial data", 
                                                                   "needs additional data"]):
                        is_l1_2 = True
                    # Check for <think> sections that might contain L1_2
                    elif "<think>" in content and "L1_2" in content:
                        is_l1_2 = True
            
            if not is_l1_2:
                logger.info(f"Query '{user_query}' not classified as L1_2, skipping DuckDB")
                return None
                
            logger.info(f"Detected L1_2 query: {user_query}")
            
            # Define specific SQL templates for common query patterns
            sql_templates = {
                "burj_khalifa_north_road": """
WITH burj_khalifa AS (
    SELECT ST_GeomFromWKB(geom_wkb) AS geometry FROM pois 
    WHERE name ILIKE '%Burj Khalifa%' OR name ILIKE '%برج خليفة%' LIMIT 1
),
nearby_properties AS (
    SELECT b.id, b.name, ST_GeomFromWKB(b.geom_wkb) AS geometry, b.address
    FROM buildings b, burj_khalifa bk
    WHERE ST_Distance(ST_GeomFromWKB(b.geom_wkb), bk.geometry) <= 2000 -- 2km radius
)
SELECT p.id, p.name, p.address, 
    ST_AsText(p.geometry) AS property_geometry,
    ST_MinX(p.geometry) AS min_x, ST_MinY(p.geometry) AS min_y,
    ST_MaxX(p.geometry) AS max_x, ST_MaxY(p.geometry) AS max_y
FROM nearby_properties p
WHERE EXISTS (
    SELECT 1 FROM roads r
    WHERE ST_Y(ST_Centroid(ST_GeomFromWKB(r.geom_wkb))) > ST_Y(ST_Centroid(p.geometry)) -- road is north of property
    AND ST_Distance(ST_GeomFromWKB(r.geom_wkb), p.geometry) <= 100 -- road is within 100m of property
)
ORDER BY ST_Distance(p.geometry, (SELECT geometry FROM burj_khalifa))
LIMIT 10;
""",
                "dubai_restaurants": """
SELECT COUNT(*) AS restaurant_count 
FROM pois 
WHERE amenity = 'restaurant' OR poi_type = 'restaurant';
""",
                "buildings_facing_roads": """
SELECT COUNT(*) AS buildings_count
FROM buildings b
WHERE EXISTS (
    SELECT 1 FROM roads r
    WHERE ST_Distance(ST_GeomFromWKB(b.geom_wkb), ST_GeomFromWKB(r.geom_wkb)) <= 50 -- within 50 meters of a road
);
"""
            }
            
            # Determine if the query matches a template pattern
            use_template = None
            lower_query = user_query.lower()
            
            if ("burj khalifa" in lower_query or "برج خليفة" in lower_query) and ("road" in lower_query and "north" in lower_query):
                use_template = "burj_khalifa_north_road"
                logger.info("Using Burj Khalifa with north road template")
            elif "restaurant" in lower_query and "dubai" in lower_query:
                use_template = "dubai_restaurants"
                logger.info("Using Dubai restaurants template")
            elif "buildings" in lower_query and "roads" in lower_query and ("facing" in lower_query or "near" in lower_query):
                use_template = "buildings_facing_roads"
                logger.info("Using buildings facing roads template")
            
            # If a template matches, use it directly
            if use_template:
                sql_query = sql_templates[use_template]
            else:
                # Generate SQL query based on user query with improved prompt engineering
                sql_generation_messages = [
                    {"role": "system", "content": f"""You are a SQL expert focused on generating DuckDB spatial SQL queries. Your ONLY job is to generate a valid SQL query that answers the user's question.

IMPORTANT:
1. Return ONLY SQL. No explanations, no thinking, no markdown, no tags.
2. The response should be JUST a valid SQL query that can be executed directly.
3. Do NOT include any text like "<think>", "Let me think", explanations, or comments about your approach.
4. Do NOT wrap the SQL in ```sql``` markdown tags.
5. Do NOT include any comments or explanations in your SQL code.

The database contains OpenStreetMap (OSM) data for Dubai with the following tables:
{', '.join([table[0] for table in self.duckdb_con.execute("SHOW TABLES").fetchall()])}

CRITICAL TABLE SCHEMA INFORMATION:
- The geometry column in all tables is named 'geom_wkb', but it's stored as a BLOB (binary data)
- You MUST convert 'geom_wkb' to a geometry using ST_GeomFromWKB(geom_wkb) before using any spatial functions
- For points of interest, use 'poi_type' instead of 'type'

Useful functions for spatial queries:
- ST_GeomFromWKB(blob) - Convert binary WKB to geometry object (REQUIRED before using any spatial functions)
- ST_Distance(geom1, geom2) - Calculate distance between geometries
- ST_Within(geom1, geom2) - Check if one geometry is within another
- ST_Intersects(geom1, geom2) - Check if geometries intersect
- ST_Buffer(geom, distance) - Create a buffer around a geometry
- ST_AsText(geom) - Convert geometry to text
- ST_X/Y(geom) - Get coordinates
- ST_Centroid(geom) - Get center point
- ST_MinX/Y/MaxX/Y(geom) - Get bounding box

Here's a schema guide:
- buildings: id, name, type, geom_wkb (BLOB), address, height
- roads: id, name, type, geom_wkb (BLOB)
- pois: id, name, poi_type, geom_wkb (BLOB), amenity (points of interest)

EXAMPLES:
For finding properties near Burj Khalifa with roads on the north side:
WITH burj_khalifa AS (
    SELECT ST_GeomFromWKB(geom_wkb) AS geometry FROM pois 
    WHERE name ILIKE '%Burj Khalifa%' LIMIT 1
),
nearby_properties AS (
    SELECT b.id, b.name, ST_GeomFromWKB(b.geom_wkb) AS geometry, b.address
    FROM buildings b, burj_khalifa bk
    WHERE ST_Distance(ST_GeomFromWKB(b.geom_wkb), bk.geometry) <= 2000
)
SELECT p.id, p.name, p.address, 
    ST_AsText(p.geometry) AS property_geometry,
    ST_MinX(p.geometry) AS min_x, ST_MinY(p.geometry) AS min_y,
    ST_MaxX(p.geometry) AS max_x, ST_MaxY(p.geometry) AS max_y
FROM nearby_properties p
WHERE EXISTS (
    SELECT 1 FROM roads r
    WHERE ST_Y(ST_Centroid(ST_GeomFromWKB(r.geom_wkb))) > ST_Y(ST_Centroid(p.geometry))
    AND ST_Distance(ST_GeomFromWKB(r.geom_wkb), p.geometry) <= 100
)
ORDER BY ST_Distance(p.geometry, (SELECT geometry FROM burj_khalifa))
LIMIT 10;"""},
                    {"role": "user", "content": f"Generate a DuckDB SQL query to answer this: {user_query}. Return ONLY SQL, no explanations or markdown."}
                ]
                
                # Get SQL query with explicit instructions
                sql_response = self.model.chat_completion(
                    messages=sql_generation_messages,
                    temperature=0.1,
                    max_tokens=800  # Increased max tokens to ensure complete queries
                )
                
                # Extract SQL query
                sql_query = None
                if isinstance(sql_response, dict):
                    # Handle dictionary response
                    if "message" in sql_response:
                        message = sql_response["message"]
                        if isinstance(message, dict) and "content" in message:
                            sql_query = message["content"].strip()
                        elif isinstance(message, str):
                            sql_query = message.strip()
                    elif "choices" in sql_response and len(sql_response["choices"]) > 0:
                        # OpenAI format
                        choice = sql_response["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            sql_query = choice["message"]["content"].strip()
                elif isinstance(sql_response, str):
                    # Handle string response directly
                    sql_query = sql_response.strip()
                    
                if not sql_query:
                    logger.warning("Failed to generate SQL query")
                    return None
                
                # Clean up the SQL query to remove any non-SQL content
                # Remove markdown triple backticks
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
                
                # Remove any text before SQL starts or after SQL ends
                sql_markers = ["SELECT ", "WITH ", "CREATE ", "INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER "]
                for marker in sql_markers:
                    if marker.lower() in sql_query.lower():
                        # Get index of marker (case insensitive)
                        start_idx = sql_query.lower().find(marker.lower())
                        sql_query = sql_query[start_idx:]
                        break
                
                # Remove thinking tags and their content
                if "<think>" in sql_query:
                    thinking_sections = sql_query.split("<think>")
                    sql_parts = []
                    for section in thinking_sections:
                        if "</think>" in section:
                            # Discard everything before </think>
                            sql_parts.append(section.split("</think>", 1)[1])
                        else:
                            sql_parts.append(section)
                    sql_query = "".join(sql_parts)
                
                # Remove any natural language text at the beginning
                thinking_patterns = [
                    "Let me think", "Here's", "I'll create", "I will", "First", "Let's", 
                    "To answer", "This query", "We need", "For this", "Step"
                ]
                
                for pattern in thinking_patterns:
                    if sql_query.startswith(pattern):
                        # Try to find first SQL keyword
                        for marker in sql_markers:
                            if marker.lower() in sql_query.lower():
                                start_idx = sql_query.lower().find(marker.lower())
                                sql_query = sql_query[start_idx:]
                                break
                        break
                
                # Check if the query looks like valid SQL
                is_valid_sql = False
                for marker in sql_markers:
                    if marker.lower() in sql_query.lower():
                        is_valid_sql = True
                        break
                
                # If query doesn't look valid or is too short, use a fallback
                if not is_valid_sql or len(sql_query) < 20:
                    logger.warning(f"Generated SQL query doesn't look valid: {sql_query[:100]}...")
                    logger.warning("Falling back to default query")
                    
                    # Default to a simple buildings count query if no pattern matched
                    sql_query = """
                    SELECT COUNT(*) AS total_buildings 
                    FROM buildings 
                    WHERE ST_X(ST_Centroid(geom_wkb)) BETWEEN 55.2 AND 55.4 
                    AND ST_Y(ST_Centroid(geom_wkb)) BETWEEN 25.1 AND 25.3;
                    """
            
            # Log the final SQL query
            logger.info(f"Generated SQL query: {sql_query}")
            
            # Generate unique query ID
            query_id = f"query_{int(time.time())}_{hash(user_query) % 10000}"
            
            # Start async query thread
            query_thread = threading.Thread(
                target=self.async_query_duckdb,
                args=(query_id, sql_query, user_query)
            )
            query_thread.daemon = True
            query_thread.start()
            
            # Track active query
            self.active_queries[query_id] = {
                "thread": query_thread,
                "start_time": time.time(),
                "user_query": user_query,
                "sql_query": sql_query
            }
            
            return query_id
            
        except Exception as e:
            logger.error(f"Error starting async DuckDB query: {e}")
            return None
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the model.
        
        Args:
            messages (List[Dict[str, str]]): List of message objects with role and content
            temperature (float): Controls randomness (0-1)
            max_tokens (int): Maximum number of tokens to generate
            tools (Optional[List[Dict[str, Any]]]): List of tools/functions available to the model
            tool_choice (str): How the model should use tools ("auto", "none", or specific tool)
            
        Returns:
            Dict[str, Any]: The model's response
        """
        try:
            logger.info(f"Sending chat completion request with {len(messages)} messages")
            
            # Start asynchronous DuckDB query if this is a user message
            query_id = None
            if len(messages) >= 1 and messages[-1]["role"] == "user":
                user_query = messages[-1]["content"]
                query_id = self.start_async_duckdb_query(user_query, messages)
                
                if query_id:
                    logger.info(f"Started async DuckDB query with ID {query_id}")
            
            # Get initial response quickly without waiting for DuckDB data
            response = self.model.chat_completion(
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Standardize response format
            standardized_response = {"message": {}}
            
            if isinstance(response, dict):
                if "error" in response and response["error"]:
                    logger.error(f"Error in chat completion: {response['error']}")
                    return {"error": response["error"]}
                
                if "message" in response:
                    message = response["message"]
                    if isinstance(message, dict) and "content" in message:
                        standardized_response["message"]["content"] = message["content"]
                    elif isinstance(message, str):
                        standardized_response["message"]["content"] = message
                    else:
                        standardized_response["message"]["content"] = str(message)
                elif "choices" in response and len(response["choices"]) > 0:
                    # OpenAI format
                    choice = response["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        standardized_response["message"]["content"] = choice["message"]["content"]
                    else:
                        standardized_response["message"]["content"] = str(choice)
                else:
                    standardized_response["message"]["content"] = str(response)
            elif isinstance(response, str):
                # Handle string response directly
                standardized_response["message"]["content"] = response
            else:
                standardized_response["message"]["content"] = str(response)
            
            # Add metadata if available
            if isinstance(response, dict) and "metadata" in response:
                standardized_response["metadata"] = response["metadata"]
            elif isinstance(response, dict) and "usage" in response:
                standardized_response["metadata"] = {"total_tokens": response["usage"].get("total_tokens", 0)}
            
            # Add query_id to response if we started an async DuckDB query
            if query_id:
                standardized_response["duckdb_query_id"] = query_id
            
            logger.info("Successfully received response from model")
            return standardized_response
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return {"error": str(e)}
    
    def get_pending_data_response(self) -> Optional[Dict[str, Any]]:
        """
        Check if there are any completed DuckDB queries with data available.
        
        Returns:
            Optional[Dict[str, Any]]: Data for improved response if available, None otherwise
        """
        try:
            if self.query_results_queue.empty():
                return None
                
            # Get next query result
            query_result = self.query_results_queue.get(block=False)
            logger.info(f"Retrieved DuckDB query result for query ID {query_result['query_id']}")
            
            # Check if query was successful
            if "result" not in query_result:
                logger.error(f"Invalid query result format - missing 'result' key")
                return {
                    "query_id": query_result["query_id"],
                    "error": "Invalid query result format"
                }
                
            if "error" in query_result["result"]:
                logger.error(f"Error in DuckDB query: {query_result['result']['error']}")
                return {
                    "query_id": query_result["query_id"],
                    "error": query_result["result"]["error"]
                }
                
            # Check if result contains data
            if "data" not in query_result["result"] or not query_result["result"]["data"]:
                logger.warning(f"DuckDB query returned no data for query ID {query_result['query_id']}")
                data_context = f"""
                I queried the Dubai database for information about your question, but no data was found.
                
                SQL Query: {query_result['sql_query']}
                
                Result: No matching records found.
                """
                return {
                    "query_id": query_result["query_id"],
                    "user_query": query_result["user_query"],
                    "data_context": data_context,
                    "no_data": True
                }
            
            # Format data context
            data_context = f"""
            I found the following data for Dubai that might help answer your question:
            
            SQL Query: {query_result['sql_query']}
            
            Results (showing up to 10 rows):
            {json.dumps(query_result['result']['data'][:10], indent=2)}
            
            Total rows: {query_result['result']['row_count']}
            """
            
            logger.info(f"Successfully formatted data for query ID {query_result['query_id']} with {query_result['result'].get('row_count', 0)} rows")
            
            return {
                "query_id": query_result["query_id"],
                "user_query": query_result["user_query"],
                "data_context": data_context
            }
            
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Error retrieving DuckDB query result: {e}")
            return None
    
    def cleanup(self):
        """Clean up model resources."""
        try:
            self.model.cleanup()
            logger.info("Model resources cleaned up")
            
            # Close DuckDB connection
            if self.duckdb_con:
                self.duckdb_con.close()
                logger.info("DuckDB connection closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def display_config(self):
        """Display the current configuration (without sensitive information)."""
        config = {
            "endpoint": self.endpoint,
            "api_key": "****" + (self.api_key[-4:] if self.api_key else ""),
            "model_name": self.model_name,
            "model_provider": self.model_provider,
            "deployment_type": self.deployment_type,
            "duckdb_path": self.duckdb_path,
            "duckdb_connected": self.duckdb_con is not None,
            "duckdb_timeout": self.duckdb_timeout
        }
        return config

def main():
    """
    Main function to demonstrate the usage of MemoryChat.
    """
    try:
        print("\n" + "=" * 60)
        print("Initializing Memory Chat with DuckDB integration for Dubai OSM data...")
        print("=" * 60)
        
        # Initialize MemoryChat
        memory_chat = MemoryChat()
        logger.info("Memory Chat initialized. Type 'exit' to quit.")
        
        # Log configuration
        config = memory_chat.display_config()
        logger.info(f"Using configuration: {config}")
        
        # Display DuckDB connection status
        duckdb_status = "connected" if config.get("duckdb_connected", False) else "not connected"
        print(f"\nDuckDB status: {duckdb_status} to {config.get('duckdb_path')}")
        
        # Set up conversation history
        messages = [
            {"role": "system", "content": """You are a helpful assistant with access to spatial and geographic data for Dubai. 

IMPORTANT: When analyzing user queries, first determine if the query needs geographic data. This is crucial for providing accurate answers.

Classify all queries into one of these categories and explicitly mention the classification in your response:
    N: Query has NO location component and can be answered by any AI model
    L0: Query HAS location component but can be answered without additional data
    L1_2: Query HAS location component and NEEDS additional geographic data

Queries that should ALWAYS be classified as L1_2 include:
- ANY query asking for specific counts, statistics or data about Dubai locations
- ANY query containing terms like "how many", "count", "find", "nearest" WITH Dubai-related terms
- ANY query asking about relationships between geographic features (e.g., buildings facing roads)
- ANY query mentioning specific Dubai landmarks (Burj Khalifa, Dubai Mall, etc.) with requests for nearby features
- ANY query asking for spatial analysis (distance, proximity, facing direction, etc.)
- ANY query asking for recommendations with bounding boxes or coordinates
- ANY query asking for "top N" POIs in Dubai

L1_2 queries require additional database queries to provide accurate information about Dubai's geography.

For EVERY user query, include your classification (N, L0, or L1_2) at the beginning of your response.

Example classifications:
"What is the capital of France?" -> L0
"How many restaurants are there in Dubai?" -> L1_2
"How to write a Python function?" -> N
"Properties near Burj Khalifa with roads on the north side" -> L1_2
"List 5 hotels in Dubai Marina" -> L1_2
"What is Dubai known for?" -> L0
"Count buildings in Downtown Dubai" -> L1_2"""
            }
        ]
        
        # Interactive chat loop
        print("\nWelcome to Memory Chat!")
        print("Type 'exit' to quit the conversation.")
        
        if config.get("duckdb_connected", False):
            print("\nFor location-based queries about Dubai, I can access Memories.")
            print("I now provide two-stage responses for location queries:")
            print("1. Initial quick response")
            print("2. Follow-up with detailed Dubai data (when available)")
            print("\nExample queries you can try:")
            print("- How many restaurants are there in Dubai?")
            print("- What are the major landmarks in Dubai?")
            print("- Show me information about parks in Dubai")
            print("- How many buildings are there within our stored database that are directly facing roads?")
            print("- Find properties near Burj Khalifa with a road on the north side")
        else:
            print("\nWarning: DuckDB connection failed. Location-based queries (L1_2) will not work properly.")
            
        print("-" * 60)
        
        # Track pending DuckDB queries
        pending_queries = {}
        
        # Query timeout in seconds (2 minutes)
        query_timeout = 120
        
        # Main chat loop
        while True:
            # Check for timed-out queries
            current_time = time.time()
            timed_out_queries = []
            
            for query_id, query_info in pending_queries.items():
                if current_time - query_info["timestamp"] > query_timeout:
                    timed_out_queries.append(query_id)
                    
            for query_id in timed_out_queries:
                logger.warning(f"Query {query_id} timed out after {query_timeout} seconds")
                print(f"\nNote: The geographic data query for your previous question has timed out. The database may be slow or unavailable.")
                del pending_queries[query_id]
            
            # First, check for any completed DuckDB queries
            data_response = memory_chat.get_pending_data_response()
            if data_response:
                query_id = data_response["query_id"]
                if "error" in data_response:
                    logger.error(f"Error processing DuckDB query {query_id}: {data_response['error']}")
                    print(f"\nNote: There was an error retrieving Dubai data for your previous query: {data_response['error']}")
                    # Remove from pending queries if it exists
                    if query_id in pending_queries:
                        del pending_queries[query_id]
                    continue
                
                # Check if this query is in our pending queries
                if query_id in pending_queries:
                    # Handle the case where no data was found
                    if data_response.get("no_data", False):
                        print("\n--- Dubai data query completed but no matching records were found ---")
                        print(data_response["data_context"])
                        del pending_queries[query_id]
                        continue
                        
                    print("\n--- Dubai data is now available! Providing enhanced response... ---")
                    
                    # Get context messages for this query
                    context_messages = pending_queries[query_id]["messages"]
                    
                    # Generate improved response
                    improved_response = memory_chat.get_response_with_data(
                        messages=context_messages,
                        data_context=data_response["data_context"]
                    )
                    
                    # Display improved response
                    if "error" not in improved_response and "message" in improved_response:
                        message_obj = improved_response["message"]
                        if isinstance(message_obj, dict) and "content" in message_obj:
                            improved_message = message_obj["content"]
                        elif isinstance(message_obj, str):
                            improved_message = message_obj
                        else:
                            improved_message = str(message_obj)
                        
                        print(f"\nAssistant (with Dubai data): {improved_message}")
                        
                        # Add to conversation history as a followup
                        context_messages.append({"role": "assistant", "content": improved_message})
                        messages = context_messages.copy()
                    else:
                        logger.error(f"Error generating response with data: {improved_response.get('error', 'Unknown error')}")
                        print("\nI had trouble processing the Dubai data. Here's what I found:")
                        print(data_response["data_context"])
                    
                    # Remove from pending queries
                    del pending_queries[query_id]
            
            # Get user input
            user_input = input("\nYou: ")
            
            # Check if user wants to exit
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
                
            # Add a special command to check pending queries
            if user_input.lower() == 'status':
                if not pending_queries:
                    print("No pending geographic data queries.")
                else:
                    print(f"\n{len(pending_queries)} pending geographic data queries:")
                    for qid, qinfo in pending_queries.items():
                        elapsed = int(time.time() - qinfo["timestamp"])
                        print(f"- Query ID: {qid}, Elapsed time: {elapsed}s, Question: {qinfo.get('user_query', 'Unknown')}")
                continue
                
            # Add a debug command to force L1_2 classification
            if user_input.lower() == 'force l1_2':
                print("Forcing L1_2 classification for the next query. Type your query now.")
                user_input = input("\nYou: ")
                # Add a special tag for the start_async_duckdb_query method to recognize
                user_input = "[FORCE_L1_2] " + user_input
            
            # Add user message to conversation
            messages.append({"role": "user", "content": user_input})
            
            # Get initial response
            response = memory_chat.chat_completion(messages)
            
            # Debug: Print full response structure
            logger.debug(f"Full response: {json.dumps(response, indent=2)}")
            
            # Check for errors
            if "error" in response and response["error"]:
                print(f"Error: {response['error']}")
                continue
            
            # Extract assistant's message
            assistant_message = None
            
            # Try different ways to extract the message based on the response structure
            if "message" in response:
                message_obj = response["message"]
                if isinstance(message_obj, dict) and "content" in message_obj:
                    assistant_message = message_obj["content"]
                elif isinstance(message_obj, str):
                    assistant_message = message_obj
                else:
                    assistant_message = str(message_obj)
            
            # If we still don't have a message, print the response structure
            if not assistant_message:
                print("\nNo content found in response. Response structure:")
                print(json.dumps(response, indent=2))
                continue
            
            # Display the assistant's message
            print(f"\nAssistant: {assistant_message}")
            
            # Add assistant's response to conversation history
            messages.append({"role": "assistant", "content": assistant_message})
            
            # If this was an L1_2 query, store context for the pending query
            if "duckdb_query_id" in response:
                query_id = response["duckdb_query_id"]
                pending_queries[query_id] = {
                    "messages": messages.copy(),
                    "timestamp": time.time(),
                    "user_query": user_input
                }
                print("\nThis query requires geographic data from Dubai. I'll provide an enhanced response when the data is available...")
                logger.info(f"Waiting for DuckDB data for query ID {query_id}")
            else:
                # Check if message contains L1_2 classification but no query was started
                if "L1_2" in assistant_message and not any(word in user_input.lower() for word in ["what is", "who is", "explain", "tell me about"]):
                    print("\nNote: The model classified this as an L1_2 query but no database query was initiated.")
                    print("This might indicate a classification/detection issue.")
                    logger.warning(f"L1_2 classification in response but no query initiated for: {user_input}")
            
            # Display token usage if available
            if "metadata" in response and "total_tokens" in response["metadata"]:
                logger.info(f"Tokens used: {response['metadata']['total_tokens']}")
        
        # Clean up resources
        memory_chat.cleanup()
    
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 

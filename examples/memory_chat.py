"""
Memory Chat Standalone Example with Memory Retrieval Integration

This module provides a simple interface to interact with AI models
for chat completion functionality with memory retrieval for Dubai OSM data.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
import duckdb
from pathlib import Path
from dotenv import load_dotenv

# Import LoadModel and MemoryRetrieval from memories package
from memories.models.load_model import LoadModel
from memories.core.memory_retrieval import MemoryRetrieval

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
    A class to interact with AI models for chat completion with memory retrieval integration.
    """
    
    def __init__(
        self,
        endpoint: str = os.getenv("MODEL_ENDPOINT"),
        api_key: str = os.getenv("MODEL_API_KEY"),
        model_name: str = os.getenv("MODEL_NAME", "gpt-4"),
        model_provider: str = os.getenv("MODEL_PROVIDER", "openai"),
        deployment_type: str = os.getenv("MODEL_DEPLOYMENT_TYPE", "api"),
        storage_path: str = os.path.expanduser("~/memories_data")
    ):
        """
        Initialize the MemoryChat with model configuration and memory retrieval.
        
        Args:
            endpoint (str): The model endpoint URL
            api_key (str): The API key for authentication
            model_name (str): The name of the model to use
            model_provider (str): The model provider (e.g., "openai", "azure-ai")
            deployment_type (str): Type of deployment (e.g., "api")
            storage_path (str): Path to store memory data
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.model_name = model_name
        self.model_provider = model_provider
        self.deployment_type = deployment_type
        self.storage_path = storage_path
        self.memory_retrieval = None
        
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
        
        # Initialize memory retrieval
        self._init_memory_retrieval()
    
    def _init_memory_retrieval(self):
        """Initialize memory retrieval."""
        try:
            self.memory_retrieval = MemoryRetrieval()
            logger.info("Successfully initialized memory retrieval")
        except Exception as e:
            logger.error(f"Failed to initialize memory retrieval: {e}")
            raise
    
    async def query_memory(self, query_type: str, spatial_input: Dict[str, Any], tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Query memory using the memory retrieval system.
        
        Args:
            query_type (str): Type of spatial query (e.g., "bbox", "address")
            spatial_input (Dict[str, Any]): Spatial input parameters
            tags (Optional[List[str]]): Optional tags for filtering
            
        Returns:
            Dict containing query results or error message
        """
        try:
            if not self.memory_retrieval:
                self._init_memory_retrieval()
                
            if not self.memory_retrieval:
                return {"error": "Could not initialize memory retrieval"}
                
            # Try retrieving from different memory tiers in order
            tiers = ["hot", "warm", "cold", "glacier"]
            result = None
            
            for tier in tiers:
                try:
                    result = await self.memory_retrieval.retrieve(
                        from_tier=tier,
                        source="osm",  # Using OSM as default source for Dubai data
                        spatial_input_type=query_type,
                        spatial_input=spatial_input,
                        tags=tags
                    )
                    if result is not None:
                        break
                except Exception as e:
                    logger.warning(f"Failed to retrieve from {tier} tier: {e}")
                    continue
            
            if result is None:
                return {"error": "No data found in any memory tier"}
            
            return {
                "success": True,
                "data": result,
                "tier": tier  # Include which tier the data came from
            }
            
        except Exception as e:
            logger.error(f"Error querying memory: {e}")
            return {"error": str(e)}
    
    async def chat_completion(
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
            
            # Check if this is an L1_2 query that needs memory retrieval
            if len(messages) >= 2 and messages[-1]["role"] == "user":
                user_query = messages[-1]["content"]
                
                # First, check if this is an L1_2 query using a simple classification
                classification_messages = [
                    {"role": "system", "content": """Analyze the following query and classify it into one of these categories:
                    N: Query has NO location component and can be answered by any AI model
                    L0: Query HAS location component but can still be answered without additional data
                    L1_2: Query HAS location component and NEEDS additional geographic data
                    
                    Return only the classification label (N, L0, or L1_2)."""},
                    {"role": "user", "content": user_query}
                ]
                
                # Get classification
                classification_response = await self.model.chat_completion(
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
                
                # Check if content contains L1_2
                if "L1_2" in content:
                    classification = "L1_2"
                
                # If L1_2 query, fetch data from memory retrieval
                if classification == "L1_2" and self.memory_retrieval:
                    logger.info(f"Detected L1_2 query: {user_query}")
                    
                    # Extract location information from query using AI
                    location_messages = [
                        {"role": "system", "content": """Extract location information from the query.
                        Return a JSON object with:
                        - lat: latitude (if mentioned or can be inferred)
                        - lon: longitude (if mentioned or can be inferred)
                        - radius: search radius in km (default to 5 if not specified)
                        - bbox: bounding box [west, south, east, north] (if mentioned)
                        - address: full address string (if mentioned)
                        
                        Return ONLY the JSON without any explanation."""},
                        {"role": "user", "content": user_query}
                    ]
                    
                    location_response = await self.model.chat_completion(
                        messages=location_messages,
                        temperature=0.0,
                        max_tokens=100
                    )
                    
                    # Extract location data
                    try:
                        if isinstance(location_response, dict) and "message" in location_response:
                            location_data = json.loads(location_response["message"]["content"])
                        else:
                            location_data = json.loads(location_response)
                            
                        # Query memory retrieval
                        if "bbox" in location_data:
                            query_result = await self.query_memory(
                                "bbox",
                                location_data["bbox"],
                                None
                            )
                        elif "address" in location_data:
                            query_result = await self.query_memory(
                                "address",
                                {"address": location_data["address"]},
                                None
                            )
                        else:
                            query_result = await self.query_memory(
                                "bbox",
                                {
                                    "lat": location_data.get("lat", 25.276987),  # Default to Dubai coordinates
                                    "lon": location_data.get("lon", 55.296233),
                                    "radius": location_data.get("radius", 5)
                                },
                                None
                            )
                        
                        if "error" not in query_result:
                            # Add data to context
                            data_context = f"""
                            I found the following data that might help answer your question:
                            
                            {json.dumps(query_result['data'], indent=2)}
                            
                            Data retrieved from {query_result['tier']} memory tier.
                            """
                            
                            # Add context to system message
                            system_message = None
                            for i, msg in enumerate(messages):
                                if msg["role"] == "system":
                                    system_message = msg
                                    messages[i]["content"] += "\n\n" + data_context
                                    break
                            
                            # If no system message, add one
                            if not system_message:
                                messages.insert(0, {
                                    "role": "system",
                                    "content": f"You are a helpful assistant with access to geographic data. {data_context}"
                                })
                    except Exception as e:
                        logger.error(f"Error processing location data: {e}")
            
            # Call LoadModel's chat_completion method
            response = await self.model.chat_completion(
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
            
            logger.info("Successfully received response from model")
            return standardized_response
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Clean up model resources."""
        try:
            self.model.cleanup()
            logger.info("Model resources cleaned up")
            
            # Close memory retrieval
            if self.memory_retrieval:
                # Close all memory tiers
                if hasattr(self.memory_retrieval, '_hot_memory') and self.memory_retrieval._hot_memory:
                    self.memory_retrieval._hot_memory.cleanup()
                if hasattr(self.memory_retrieval, '_warm_memory') and self.memory_retrieval._warm_memory:
                    self.memory_retrieval._warm_memory.cleanup()
                if hasattr(self.memory_retrieval, '_cold_memory') and self.memory_retrieval._cold_memory:
                    self.memory_retrieval._cold_memory.cleanup()
                if hasattr(self.memory_retrieval, '_red_hot_memory') and self.memory_retrieval._red_hot_memory:
                    self.memory_retrieval._red_hot_memory.cleanup()
                # Close glacier connectors
                if hasattr(self.memory_retrieval, '_glacier_memory'):
                    for connector in self.memory_retrieval._glacier_memory.values():
                        if hasattr(connector, 'cleanup'):
                            connector.cleanup()
                logger.info("Memory retrieval closed")
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
            "storage_path": self.storage_path,
            "memory_retrieval_connected": self.memory_retrieval is not None
        }
        return config

async def main():
    """
    Main function to demonstrate the usage of MemoryChat.
    """
    try:
        print("\n" + "=" * 60)
        print("Initializing Memory Chat with memory retrieval integration for Dubai OSM data...")
        print("=" * 60)
        
        # Initialize MemoryChat
        memory_chat = MemoryChat()
        logger.info("Memory Chat initialized. Type 'exit' to quit.")
        
        # Log configuration
        config = memory_chat.display_config()
        logger.info(f"Using configuration: {config}")
        
        # Display memory retrieval connection status
        memory_retrieval_status = "connected" if config.get("memory_retrieval_connected", False) else "not connected"
        print(f"\nMemory retrieval status: {memory_retrieval_status} to {config.get('storage_path')}")
        
        # Set up conversation history
        messages = [
            {"role": "system", "content": "You are a helpful assistant. " + 
            """Analyze the following query and classify it into one of these categories:
    N: Query has NO location component and can be answered by any AI model
    L0: Query HAS location component but can still be answered without additional data
    L1_2: Query HAS location component and NEEDS additional geographic data

    Examples:
    "What is the capital of France?" -> L0 (has location but needs no additional data)
    "What restaurants are near me?" -> L1_2 (needs actual location data)
    "How do I write a Python function?" -> N (no location component)
    "Tell me about Central Park" -> L0 (has location but needs no additional data)
    "Find cafes within 2km of Times Square" -> L1_2 (needs additional geographic data)
    
    For each user query, first classify it and then respond accordingly. For L1_2 queries, I will use memories for Dubai to provide relevant information."""}
        ]
        
        # Interactive chat loop
        print("\nWelcome to Memory Chat!")
        print("Type 'exit' to quit the conversation.")
        
        if config.get("memory_retrieval_connected", False):
            print("\nFor location-based queries about Dubai, I can access Memories ")
            print("Example queries you can try:")
            print("- How many restaurants are there in Dubai?")
            print("- What are the major landmarks in Dubai?")
            print("- Show me information about parks in Dubai")
        else:
            print("\nWarning: Memory retrieval connection failed. Location-based queries (L1_2) will not work properly.")
            
        print("-" * 60)
        
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check if user wants to exit
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
            
            # Add user message to conversation
            messages.append({"role": "user", "content": user_input})
            
            # Get response
            response = await memory_chat.chat_completion(messages)
            
            # Debug: Print full response structure
            logger.debug(f"Full response: {json.dumps(response, indent=2)}")
            
            # Process and display the response
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
            
            # Display token usage if available
            if "metadata" in response and "total_tokens" in response["metadata"]:
                logger.info(f"Tokens used: {response['metadata']['total_tokens']}")
        
        # Clean up resources
        memory_chat.cleanup()
    
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 
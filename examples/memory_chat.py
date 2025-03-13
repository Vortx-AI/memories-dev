"""
Memory Chat Example 

This module provides a simple interface to interact with AI models
for chat completion functionality using the LoadModel class.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("examples/memory_chat.log")
    ]
)
logger = logging.getLogger(__name__)

# Import LoadModel
from memories.models.load_model import LoadModel

class MemoryChat:
    """
    A class to interact with  AI models for chat completion.
    """
    
    def __init__(
        self,
        endpoint: str = os.getenv("MODEL_ENDPOINT"),
        api_key: str = os.getenv("MODEL_API_KEY"),
        model_name: str = os.getenv("MODEL_NAME"),
        model_provider: str = os.getenv("MODEL_PROVIDER"),
        deployment_type: str = os.getenv("MODEL_DEPLOYMENT_TYPE")
    ):
        """
        Initialize the MemoryChat with Azure AI configuration.
        
        Args:
            endpoint (str): The Azure AI endpoint URL
            api_key (str): The API key for authentication
            model_name (str): The name of the model to use
            model_provider (str): The model provider (e.g., "azure-ai")
            deployment_type (str): Type of deployment (e.g., "api")
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.model_name = model_name
        
        # Validate required configuration
        if not self.endpoint or not self.api_key:
            logger.error("Missing required environment variables: AZURE_AI_ENDPOINT or AZURE_AI_API_KEY")
            raise ValueError("Missing required environment variables. Please check your .env file.")
        
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
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the Azure AI model.
        
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
            
            # Call LoadModel's chat_completion method
            response = self.model.chat_completion(
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if "error" in response and response["error"]:
                logger.error(f"Error in chat completion: {response['error']}")
                return {"error": response["error"]}
            
            logger.info("Successfully received response from model")
            return response
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Clean up model resources."""
        try:
            self.model.cleanup()
            logger.info("Model resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def display_config(self):
        """Display the current configuration (without sensitive information)."""
        config = {
            "endpoint": self.endpoint,
            "api_key": "****" + (self.api_key[-4:] if self.api_key else ""),
            "model_name": self.model_name,
        }
        return config

def main():
    """
    Main function to demonstrate the usage of MemoryChat.
    """
    try:
        # Initialize MemoryChat
        memory_chat = MemoryChat()
        logger.info("Memory Chat initialized. Type 'exit' to quit.")
        
        # Log configuration
        logger.info(f"Using configuration: {memory_chat.display_config()}")
        
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
    
    For each user query, first classify it and then respond accordingly."""}
        ]
        
        # Interactive chat loop
        print("\nWelcome to Memory Chat!")
        print("Type 'exit' to quit the conversation.")
        print("-" * 50)
        
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
            response = memory_chat.chat_completion(messages)
            
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
    main()
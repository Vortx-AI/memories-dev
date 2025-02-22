from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from memories.agents.agent import Agent
from memories.models.load_model import LoadModel
from memories.agents.agent_geocoder import AgentGeocoder  # For location validation
import logging
import os
from dotenv import load_dotenv
import json

@dataclass
class Message:
    """Represents a single message in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]  # Stores classification, location info, etc.

class ConversationContext:
    """Manages conversation state and history"""
    def __init__(self):
        self.messages: List[Message] = []
        self.current_location: Optional[Dict[str, Any]] = None
        self.last_query_type: Optional[str] = None
        self.active_context: Optional[Dict[str, Any]] = None
    
    def set_location(self, location: Dict[str, Any]) -> None:
        """
        Set the current location context
        
        Args:
            location (Dict[str, Any]): Location info containing coordinates or place details
        """
        self.current_location = location
        # Add a system message about location change
        self.add_message(
            'system',
            f"Location set to: {location.get('display_name', str(location))}",
            metadata={'location_update': location}
        )
    
    def get_current_location(self) -> Optional[Dict[str, Any]]:
        """Get the current location context"""
        return self.current_location
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to the conversation history"""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.messages.append(message)
    
    def update_context(self, location: Optional[Dict[str, Any]] = None, 
                      query_type: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None):
        """Update the conversation context"""
        if location:
            self.current_location = location
        if query_type:
            self.last_query_type = query_type
        if context:
            self.active_context = context
    
    def get_recent_context(self, num_messages: int = 5) -> List[Message]:
        """Get the most recent messages for context"""
        return self.messages[-num_messages:] if self.messages else []
    
    def save_conversation(self, filepath: str):
        """Save conversation history to file"""
        data = {
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in self.messages
            ],
            'context': {
                'current_location': self.current_location,
                'last_query_type': self.last_query_type,
                'active_context': self.active_context
            }
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

class LocationAwareChatbot:
    def __init__(self):
        """Initialize the location-aware chatbot"""
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize conversation context
        self.context = ConversationContext()
        
        # Initialize the main agent and geocoder
        self.agent = Agent(
            modalities={},  # Will be expanded for location data
            memories={}
        )
        self.geocoder = AgentGeocoder()
    
    def set_location(self, location_input: str) -> Dict[str, Any]:
        """
        Set the current location for subsequent queries
        
        Args:
            location_input (str): Location string (address, coordinates, place name)
            
        Returns:
            Dict[str, Any]: Response indicating success/failure and location details
        """
        try:
            # Validate and geocode the location
            location_info = self.geocoder.geocode(location_input)
            
            if not location_info:
                return {
                    "success": False,
                    "error": "Could not validate location",
                    "response": "I couldn't find that location. Please try again with a different location."
                }
            
            # Update the conversation context with the new location
            self.context.set_location(location_info)
            
            return {
                "success": True,
                "location": location_info,
                "response": f"Location set to: {location_info.get('display_name', location_input)}"
            }
            
        except Exception as e:
            self.logger.error(f"Error setting location: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "There was an error setting the location."
            }
    
    def process_message(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user message with context awareness
        
        Args:
            user_input (str): The user's message
            
        Returns:
            Dict[str, Any]: Processed response with classification and context
        """
        try:
            # Check if this is a location setting command
            if user_input.lower().startswith(('set location', 'location:', 'at location')):
                location_input = user_input.split(':', 1)[-1].strip()
                if not location_input:
                    location_input = user_input.split('location', 1)[-1].strip()
                return self.set_location(location_input)
            
            # Add user message to context
            self.context.add_message('user', user_input)
            
            # Get recent conversation context
            recent_context = self.context.get_recent_context()
            
            # Get current location
            current_location = self.context.get_current_location()
            
            # Process query with agent, including location context
            response = self.agent.process_query(
                query=user_input,
                memories={
                    'location_context': current_location,
                    'conversation_history': recent_context
                }
            )
            
            # Update conversation context based on response
            if 'classification' in response:
                self.context.update_context(
                    query_type=response['classification']
                )
            
            # Add assistant's response to context
            self.context.add_message('assistant', 
                                   response.get('response', ''),
                                   metadata=response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            error_response = {
                "error": str(e),
                "classification": None,
                "response": "I encountered an error processing your message."
            }
            self.context.add_message('assistant', 
                                   error_response['response'],
                                   metadata=error_response)
            return error_response

    def format_response(self, response: Dict[str, Any]) -> str:
        """Format the response for display"""
        formatted = []
        
        # Handle location setting response
        if 'success' in response:
            return response['response']
        
        # Add current location context if available
        current_location = self.context.get_current_location()
        if current_location:
            formatted.append(f"Current Location: {current_location.get('display_name', 'Unknown')}")
        
        # Add query classification
        if 'classification' in response:
            formatted.append(f"Type: {response['classification']}")
        
        # Add location information if present
        if 'location_details' in response:
            loc_details = response['location_details']
            formatted.append("\nLocation Information:")
            formatted.append(f"• Type: {loc_details.get('data_type', 'N/A')}")
            if loc_info := loc_details.get('location_info'):
                formatted.append(f"• Location: {loc_info.get('location', 'N/A')}")
                formatted.append(f"• Location Type: {loc_info.get('location_type', 'N/A')}")
        
        # Add the main response
        if 'response' in response:
            formatted.append(f"\n{response['response']}")
        
        return "\n".join(formatted)

def main():
    """Run the interactive chat session"""
    print("\nInitializing Location-Aware Chatbot...")
    chatbot = LocationAwareChatbot()
    
    print("\nChatbot initialized! Type 'quit' to exit.")
    print("Type 'save' to save conversation.")
    print("Type 'set location: <place>' to set a location.")
    print("="*50)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'quit':
            print("\nGoodbye!")
            break
        
        if user_input.lower() == 'save':
            chatbot.context.save_conversation('conversation_history.json')
            print("Conversation saved!")
            continue
        
        response = chatbot.process_message(user_input)
        print("\nBot:", chatbot.format_response(response))

if __name__ == "__main__":
    main() 
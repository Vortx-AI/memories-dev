import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
print(f"Added {project_root} to Python path")

class Chatbot:
    """Simple chatbot implementation"""
    def __init__(self):
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

    def process_message(self, user_input: str) -> Dict[str, Any]:
        """Process a user message and return a response"""
        try:
            self.logger.info(f"Processing query: {user_input}")
            
            # For now, just return the query information
            return {
                "query": user_input,
                "timestamp": datetime.now().isoformat(),
                "status": "received"
            }
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self.logger.error(error_msg)
            return {
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }

def main():
    """Run the interactive chat session"""
    print("\nWelcome to the Chatbot!")
    
    try:
        print("\nInitializing Chatbot...")
        chatbot = Chatbot()
        
        print("\nChatbot initialized! Type 'quit' to exit.")
        print("="*50)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'quit':
                    print("\nGoodbye!")
                    break
                
                response = chatbot.process_message(user_input)
                print("\nBot:", response)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
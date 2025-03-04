import asyncio
import logging
import sys
import aioconsole
from .interface import WebRTCInterface, WebRTCClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class ChatServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.server = WebRTCInterface(host=host, port=port)
        self.messages = []
        
    def setup(self):
        # Register chat functions
        self.server.register_function(self.send_message)
        self.server.register_function(self.get_messages)
        
    async def send_message(self, username: str, message: str) -> bool:
        """Handle incoming chat messages."""
        formatted_msg = f"{username}: {message}"
        self.messages.append(formatted_msg)
        logger.info(f"New message: {formatted_msg}")
        return True
        
    async def get_messages(self, since_index: int = 0) -> list:
        """Get messages since a given index."""
        return self.messages[since_index:]
        
    def start(self):
        """Start the chat server."""
        self.setup()
        self.server.start()
        
    def stop(self):
        """Stop the chat server."""
        self.server.stop()

class ChatClient:
    def __init__(self, username: str, host: str = "localhost", port: int = 8765):
        self.username = username
        self.client = WebRTCClient(host=host, port=port)
        self.last_message_index = 0
        self._running = False
        
    async def connect(self):
        """Connect to the chat server."""
        await self.client.connect()
        
    async def send_message(self, message: str):
        """Send a chat message."""
        try:
            await self.client.call_function("send_message", self.username, message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            
    async def fetch_new_messages(self):
        """Fetch new messages from the server."""
        try:
            messages = await self.client.call_function("get_messages", self.last_message_index)
            if messages:
                for msg in messages:
                    # Only print messages from others (our own messages are printed when sent)
                    if not msg.startswith(f"{self.username}: "):
                        print(f"\r{msg}")
                self.last_message_index += len(messages)
                
                # Redraw the input prompt
                print("> ", end="", flush=True)
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            
    async def message_loop(self):
        """Main message loop for sending messages."""
        self._running = True
        print("Chat started. Type your messages (or 'quit' to exit):")
        
        while self._running:
            try:
                message = await aioconsole.ainput("> ")
                if message.lower() in ('quit', 'exit'):
                    self._running = False
                    break
                    
                if message:
                    await self.send_message(message)
                    
            except EOFError:
                self._running = False
                break
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                
    async def update_loop(self):
        """Background loop for fetching new messages."""
        while self._running:
            await self.fetch_new_messages()
            await asyncio.sleep(0.5)  # Check for new messages every 0.5 seconds
            
    async def run(self):
        """Run the chat client."""
        try:
            await self.connect()
            # Start the update loop in the background
            update_task = asyncio.create_task(self.update_loop())
            # Run the main message loop
            await self.message_loop()
            # Cancel the update loop when we're done
            update_task.cancel()
            try:
                await update_task
            except asyncio.CancelledError:
                pass
        finally:
            await self.client.close()

async def run_server():
    """Run the chat server."""
    server = ChatServer()
    server.start()
    
    try:
        logger.info("Chat server is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down chat server...")
    finally:
        server.stop()

async def run_client(username: str):
    """Run the chat client."""
    client = ChatClient(username)
    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("Chat client stopped by user")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Server: python -m memories.interface.webrtc.chat server")
        print("  Client: python -m memories.interface.webrtc.chat client <username>")
        sys.exit(1)
        
    if sys.argv[1] == "server":
        try:
            asyncio.run(run_server())
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
    elif sys.argv[1] == "client":
        if len(sys.argv) < 3:
            print("Error: Username required for client")
            print("Usage: python -m memories.interface.webrtc.chat client <username>")
            sys.exit(1)
        try:
            asyncio.run(run_client(sys.argv[2]))
        except KeyboardInterrupt:
            logger.info("Client stopped by user")
    else:
        print("Invalid argument. Use 'server' or 'client'")
        sys.exit(1) 
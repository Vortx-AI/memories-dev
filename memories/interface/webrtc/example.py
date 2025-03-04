import asyncio
import logging
from .interface import WebRTCInterface, WebRTCClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Example function to be exposed through WebRTC
def add_numbers(a: float, b: float) -> float:
    logger.info(f"Adding numbers: {a} + {b}")
    return a + b

async def run_server():
    # Create and start the WebRTC interface
    server = WebRTCInterface(host="0.0.0.0", port=8765)
    
    # Register the function we want to expose
    server.register_function(add_numbers)
    
    # Start the server
    server.start()
    
    try:
        logger.info("Server is running. Press Ctrl+C to stop.")
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        server.stop()

async def run_client():
    # Create and connect the client
    client = WebRTCClient(host="localhost", port=8765)
    
    try:
        logger.info("Connecting to server...")
        await client.connect()
        
        # Call the remote function
        a, b = 5, 3
        logger.info(f"Calling add_numbers({a}, {b})")
        result = await client.call_function("add_numbers", a, b)
        logger.info(f"Result: {a} + {b} = {result}")
        
    except ConnectionError as e:
        logger.error(f"Failed to connect to server: {e}")
    except Exception as e:
        logger.error(f"Error during client operation: {e}")
    finally:
        await client.close()

# Example of how to run the server
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m memories.interface.webrtc.example [server|client]")
        sys.exit(1)
        
    if sys.argv[1] == "server":
        try:
            asyncio.run(run_server())
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
    elif sys.argv[1] == "client":
        try:
            asyncio.run(run_client())
        except KeyboardInterrupt:
            logger.info("Client stopped by user")
    else:
        print("Invalid argument. Use 'server' or 'client'")
        sys.exit(1) 
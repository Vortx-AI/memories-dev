# WebRTC Interface

This module provides a simple WebRTC interface for exposing Python functions through WebRTC data channels, along with a sample chat application.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Components

### 1. WebRTC Interface (`interface.py`)
The core WebRTC implementation that allows exposing Python functions through WebRTC data channels.

```python
from memories.interface.webrtc import WebRTCInterface, WebRTCClient

# Server side
server = WebRTCInterface(host="0.0.0.0", port=8765)
server.register_function(your_function)
server.start()

# Client side
client = WebRTCClient(host="localhost", port=8765)
await client.connect()
result = await client.call_function("your_function", *args, **kwargs)
```

### 2. Chat Application (`chat.py`)
A sample chat application built using the WebRTC interface.

To run the chat server:
```bash
python -m memories.interface.webrtc.chat server
```

To run a chat client:
```bash
python -m memories.interface.webrtc.chat client <username>
```

## Features

- Real-time peer-to-peer communication using WebRTC
- Simple function registration and remote calling
- Automatic JSON serialization of arguments and results
- Support for both synchronous and asynchronous functions
- Built-in signaling server for WebRTC connection establishment
- Clean error handling and connection management
- Example chat application with real-time messaging

## Example Usage

### Exposing a Python Function

```python
from memories.interface.webrtc import WebRTCInterface

# Create a function to expose
async def add_numbers(a: float, b: float) -> float:
    return a + b

# Create and start the server
server = WebRTCInterface()
server.register_function(add_numbers)
server.start()
```

### Calling the Function from a Client

```python
from memories.interface.webrtc import WebRTCClient

async def main():
    # Connect to the server
    client = WebRTCClient()
    await client.connect()
    
    # Call the remote function
    result = await client.call_function("add_numbers", 5, 3)
    print(f"5 + 3 = {result}")
    
    await client.close()

asyncio.run(main())
```

## Security Considerations

- The WebRTC connection is encrypted by default
- The signaling server uses TCP for initial connection setup
- Function calls are validated on the server side
- Error messages are sanitized before being sent to clients

## Requirements

See `requirements.txt` for the complete list of dependencies. 
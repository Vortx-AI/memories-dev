import asyncio
import json
import logging
import socket
from typing import Any, Callable, Dict, Optional, Union
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
from aiortc.contrib.signaling import TcpSocketSignaling
import threading
import queue
import functools

logger = logging.getLogger(__name__)

class SignalingServer:
    """A simple TCP signaling server for WebRTC."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self._sock = None
        self._running = False
        
    def start(self) -> None:
        """Start the signaling server."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(1)
        self._running = True
        logger.info(f"Signaling server listening on {self.host}:{self.port}")
        
    def stop(self) -> None:
        """Stop the signaling server."""
        self._running = False
        if self._sock:
            self._sock.close()
            self._sock = None

class WebRTCInterface:
    """A WebRTC interface that allows exposing Python functions through WebRTC data channels."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        """
        Initialize the WebRTC interface.
        
        Args:
            host: The host to bind the signaling server to
            port: The port to bind the signaling server to
        """
        self.host = host
        self.port = port
        self.pc = None
        self.signaling = None
        self.data_channel = None
        self._registered_functions: Dict[str, Callable] = {}
        self._message_queue = queue.Queue()
        self._running = False
        self._signaling_server = SignalingServer(host, port)
        
    def register_function(self, func: Callable, name: Optional[str] = None) -> None:
        """
        Register a Python function to be exposed through WebRTC.
        
        Args:
            func: The function to register
            name: Optional name for the function. If not provided, uses the function's name
        """
        if name is None:
            name = func.__name__
        self._registered_functions[name] = func
        
    async def _handle_data_channel(self, channel: RTCDataChannel) -> None:
        """Handle incoming data channel messages."""
        
        @channel.on("message")
        async def on_message(message: Union[str, bytes]) -> None:
            if isinstance(message, bytes):
                message = message.decode()
                
            try:
                data = json.loads(message)
                func_name = data.get("function")
                args = data.get("args", [])
                kwargs = data.get("kwargs", {})
                request_id = data.get("request_id")
                
                if func_name not in self._registered_functions:
                    response = {
                        "error": f"Function {func_name} not found",
                        "request_id": request_id
                    }
                else:
                    try:
                        func = self._registered_functions[func_name]
                        if asyncio.iscoroutinefunction(func):
                            result = await func(*args, **kwargs)
                        else:
                            result = func(*args, **kwargs)
                        
                        response = {
                            "result": result,
                            "request_id": request_id
                        }
                    except Exception as e:
                        response = {
                            "error": str(e),
                            "request_id": request_id
                        }
                
                await channel.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message received: {message}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                
    async def _run_server(self) -> None:
        """Run the WebRTC server."""
        # Start the signaling server first
        self._signaling_server.start()
        
        try:
            self.signaling = TcpSocketSignaling(self.host, self.port)
            
            while self._running:
                self.pc = RTCPeerConnection()
                
                @self.pc.on("datachannel")
                def on_datachannel(channel):
                    self.data_channel = channel
                    asyncio.create_task(self._handle_data_channel(channel))
                
                # Wait for the client to connect
                try:
                    offer = await self.signaling.receive()
                    await self.pc.setRemoteDescription(offer)
                    
                    answer = await self.pc.createAnswer()
                    await self.pc.setLocalDescription(answer)
                    
                    await self.signaling.send(self.pc.localDescription)
                    
                    # Wait for connection to close
                    await self.pc.wait_closed()
                    
                except Exception as e:
                    logger.error(f"Error in WebRTC server: {e}")
                finally:
                    if self.pc:
                        await self.pc.close()
        finally:
            self._signaling_server.stop()
                    
    def start(self) -> None:
        """Start the WebRTC server in a background thread."""
        if self._running:
            return
            
        self._running = True
        
        def run_event_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_server())
            
        self._thread = threading.Thread(target=run_event_loop, daemon=True)
        self._thread.start()
        logger.info(f"WebRTC server started on {self.host}:{self.port}")
        
    def stop(self) -> None:
        """Stop the WebRTC server."""
        self._running = False
        if self.pc:
            asyncio.run(self.pc.close())
        if self.signaling:
            self.signaling.close()
        self._signaling_server.stop()
            
class WebRTCClient:
    """Client for connecting to a WebRTC interface."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize the WebRTC client.
        
        Args:
            host: The host of the signaling server
            port: The port of the signaling server
        """
        self.host = host
        self.port = port
        self.pc = None
        self.signaling = None
        self.data_channel = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
    async def connect(self) -> None:
        """Connect to the WebRTC server."""
        try:
            self.signaling = TcpSocketSignaling(self.host, self.port)
            self.pc = RTCPeerConnection()
            
            self.data_channel = self.pc.createDataChannel("data")
            
            @self.data_channel.on("message")
            async def on_message(message: Union[str, bytes]) -> None:
                if isinstance(message, bytes):
                    message = message.decode()
                    
                try:
                    data = json.loads(message)
                    request_id = data.get("request_id")
                    
                    if request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        if "error" in data:
                            future.set_exception(Exception(data["error"]))
                        else:
                            future.set_result(data.get("result"))
                            
                except Exception as e:
                    logger.error(f"Error handling response: {e}")
                    
            # Create offer
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            # Send offer and get answer
            await self.signaling.send(self.pc.localDescription)
            answer = await self.signaling.receive()
            
            await self.pc.setRemoteDescription(answer)
            logger.info("Connected to WebRTC server")
            
        except Exception as e:
            logger.error(f"Error connecting to WebRTC server: {e}")
            await self.close()
            raise
        
    async def call_function(self, func_name: str, *args, **kwargs) -> Any:
        """
        Call a function on the remote server.
        
        Args:
            func_name: Name of the function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function call
        """
        if not self.data_channel or self.data_channel.readyState != "open":
            raise ConnectionError("Not connected to server")
            
        request_id = f"{func_name}_{id(args)}_{id(kwargs)}"
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        message = {
            "function": func_name,
            "args": args,
            "kwargs": kwargs,
            "request_id": request_id
        }
        
        await self.data_channel.send(json.dumps(message))
        return await future
        
    async def close(self) -> None:
        """Close the WebRTC connection."""
        if self.pc:
            await self.pc.close()
        if self.signaling:
            self.signaling.close() 
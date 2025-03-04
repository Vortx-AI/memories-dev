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
        self._client_sock = None
        logger.info(f"SignalingServer initialized with host={host}, port={port}")
        
    def start(self) -> None:
        """Start the signaling server."""
        try:
            logger.info("Creating socket...")
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Server socket should not timeout since it's in a background thread
            self._sock.settimeout(None)
            
            logger.info(f"Binding to {self.host}:{self.port}...")
            try:
                self._sock.bind((self.host, self.port))
            except socket.error as e:
                logger.error(f"❌ Bind failed: {e}")
                raise
            
            logger.info("Starting to listen...")
            try:
                self._sock.listen(1)
                logger.info(f"✅ Signaling server listening on {self.host}:{self.port}")
                self._running = True
                
                while self._running:
                    try:
                        # Accept one connection
                        logger.info("Waiting for client connection...")
                        self._client_sock, addr = self._sock.accept()
                        logger.info(f"Client connected from {addr}")
                        
                        # Only set timeout for client operations
                        self._client_sock.settimeout(300)  # 5 minute timeout for client operations
                        
                        # Handle the client connection
                        # TODO: Add proper client handling here
                        # For now, just keep the connection open
                        while self._running:
                            try:
                                data = self._client_sock.recv(1024)
                                if not data:
                                    break
                            except socket.timeout:
                                continue
                            except Exception as e:
                                logger.error(f"Error handling client: {e}")
                                break
                                
                        # Close client socket when done
                        self._client_sock.close()
                        self._client_sock = None
                        
                    except Exception as e:
                        logger.error(f"Error accepting client: {e}")
                        if self._client_sock:
                            self._client_sock.close()
                            self._client_sock = None
                
            except socket.error as e:
                logger.error(f"❌ Listen/Accept failed: {e}")
                raise
                
        except Exception as e:
            logger.error(f"❌ Failed to start signaling server: {e}")
            if self._sock:
                self._sock.close()
                self._sock = None
            raise
        
    def stop(self) -> None:
        """Stop the signaling server."""
        logger.info("Stopping signaling server...")
        self._running = False
        if self._client_sock:
            try:
                self._client_sock.close()
                logger.info("Client socket closed")
            except Exception as e:
                logger.error(f"Error closing client socket: {e}")
        if self._sock:
            try:
                self._sock.close()
                logger.info("Server socket closed")
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")
            finally:
                self._sock = None
                self._client_sock = None

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
        logger.info(f"Creating SignalingServer on {host}:{port}")
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
        logger.info("Starting signaling server...")
        self._signaling_server.start()
        
        try:
            logger.info("Creating TcpSocketSignaling...")
            self.signaling = TcpSocketSignaling(self.host, self.port)
            
            while self._running:
                logger.info("Creating new RTCPeerConnection...")
                self.pc = RTCPeerConnection()
                
                @self.pc.on("datachannel")
                def on_datachannel(channel):
                    logger.info(f"New data channel: {channel.label}")
                    self.data_channel = channel
                    asyncio.create_task(self._handle_data_channel(channel))
                
                # Wait for the client to connect
                try:
                    logger.info("Waiting for client offer...")
                    offer = await self.signaling.receive()
                    logger.info("Received offer, setting remote description...")
                    await self.pc.setRemoteDescription(offer)
                    
                    logger.info("Creating answer...")
                    answer = await self.pc.createAnswer()
                    logger.info("Setting local description...")
                    await self.pc.setLocalDescription(answer)
                    
                    logger.info("Sending answer...")
                    await self.signaling.send(self.pc.localDescription)
                    logger.info("✅ Connection established!")
                    
                    # Wait for connection to close
                    await self.pc.wait_closed()
                    
                except Exception as e:
                    logger.error(f"❌ Error in WebRTC server: {e}")
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
        """Initialize the WebRTC client."""
        self.host = host
        self.port = port
        self.pc = None
        self.signaling = None
        self.data_channel = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        logger.info(f"WebRTCClient initialized for {host}:{port}")
        
    async def connect(self) -> None:
        """Connect to the WebRTC server."""
        try:
            # Create a custom signaling class that doesn't try to bind
            class ClientSignaling(TcpSocketSignaling):
                def __init__(self, host, port):
                    self.host = host
                    self.port = port
                    self._sock = None
                    self._recv_queue = None
                    self._send_queue = None
                    self._runner = None
                    logger.info(f"ClientSignaling initialized for {host}:{port}")
                    
                async def connect(self):
                    logger.info(f"Attempting to connect to {self.host}:{self.port}...")
                    try:
                        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self._sock.settimeout(300)  # 300 second timeout
                        await asyncio.get_event_loop().sock_connect(self._sock, (self.host, self.port))
                        logger.info("Socket connection established")
                        self._recv_queue = asyncio.Queue()
                        self._send_queue = asyncio.Queue()
                        self._runner = asyncio.ensure_future(self._run())
                    except Exception as e:
                        logger.error(f"Failed to connect to signaling server: {e}")
                        if self._sock:
                            self._sock.close()
                        raise
                            
                async def _run(self):
                    try:
                        while True:
                            # Handle receiving
                            try:
                                data = await self._recv()
                                if data:
                                    logger.info(f"Received data: {len(data)} bytes")
                                    await self._recv_queue.put(data)
                            except asyncio.TimeoutError:
                                logger.error("Receive timeout")
                                break
                            except Exception as e:
                                logger.error(f"Error receiving data: {e}")
                                break
                                
                            # Handle sending
                            try:
                                if not self._send_queue.empty():
                                    data = await self._send_queue.get()
                                    await self._send(data)
                                    logger.info(f"Sent data: {len(data)} bytes")
                            except Exception as e:
                                logger.error(f"Error sending data: {e}")
                                break
                            
                            # Small delay to prevent busy loop
                            await asyncio.sleep(0.1)
                            
                    except Exception as e:
                        logger.error(f"Error in signaling loop: {e}")
                    finally:
                        if self._sock:
                            self._sock.close()
                            
                async def _send(self, data):
                    """Send data on the socket."""
                    if not self._sock:
                        raise ConnectionError("Not connected")
                    await asyncio.get_event_loop().sock_sendall(self._sock, data)
                    
                async def _recv(self):
                    """Receive data from the socket."""
                    if not self._sock:
                        raise ConnectionError("Not connected")
                    try:
                        data = await asyncio.wait_for(
                            asyncio.get_event_loop().sock_recv(self._sock, 65536),
                            timeout=300
                        )
                        if not data:
                            raise ConnectionError("Connection closed by remote peer")
                        return data
                    except asyncio.TimeoutError:
                        logger.error("Receive operation timed out")
                        raise
                    
                async def send(self, descr):
                    """Send a description."""
                    data = json.dumps({"type": descr.type, "sdp": descr.sdp}).encode()
                    await self._send_queue.put(data + b"\n")
                    
                async def receive(self):
                    """Receive a description."""
                    try:
                        data = await asyncio.wait_for(self._recv_queue.get(), timeout=300)
                        data = json.loads(data.decode())
                        return RTCSessionDescription(type=data["type"], sdp=data["sdp"])
                    except asyncio.TimeoutError:
                        logger.error("Timeout waiting for description")
                        raise
            
            # Initialize signaling with the remote server
            logger.info(f"Creating signaling connection to {self.host}:{self.port}")
            self.signaling = ClientSignaling(self.host, self.port)
            await self.signaling.connect()
            
            logger.info("Creating RTCPeerConnection")
            self.pc = RTCPeerConnection()
            self.data_channel = self.pc.createDataChannel("data")
            
            @self.data_channel.on("open")
            def on_open():
                logger.info("Data channel opened")
                
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
            logger.info("Creating connection offer")
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            # Send offer and get answer
            logger.info("Sending offer to server")
            await self.signaling.send(self.pc.localDescription)
            logger.info("Waiting for server answer")
            answer = await self.signaling.receive()
            
            logger.info("Setting remote description")
            await self.pc.setRemoteDescription(answer)
            logger.info("✅ Connected to WebRTC server")
            
        except Exception as e:
            logger.error(f"❌ Error connecting to WebRTC server: {e}")
            if self.signaling:
                await self.signaling.close()
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
        logger.info("Closing WebRTC connection...")
        if self.pc:
            await self.pc.close()
        if self.signaling:
            await self.signaling.close()
        logger.info("Connection closed") 
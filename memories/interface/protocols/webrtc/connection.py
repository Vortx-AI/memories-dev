"""
WebRTC connection handler for managing peer connections and data channels.
"""
from typing import Optional, Callable, Dict, Any
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class WebRTCConnection:
    def __init__(self):
        self.peer_connection: Optional[RTCPeerConnection] = None
        self.data_channel: Optional[RTCDataChannel] = None
        self._message_handlers: Dict[str, Callable] = {}
        
    async def create_peer_connection(self) -> RTCPeerConnection:
        """Create and initialize a new WebRTC peer connection."""
        self.peer_connection = RTCPeerConnection()
        
        @self.peer_connection.on("datachannel")
        def on_datachannel(channel: RTCDataChannel):
            self.data_channel = channel
            self._setup_data_channel(channel)
            
        @self.peer_connection.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state changed to: {self.peer_connection.connectionState}")
            
        return self.peer_connection
    
    def _setup_data_channel(self, channel: RTCDataChannel):
        """Set up event handlers for the data channel."""
        @channel.on("message")
        async def on_message(message: str):
            try:
                data = json.loads(message)
                message_type = data.get("type")
                if message_type in self._message_handlers:
                    await self._message_handlers[message_type](data)
            except json.JSONDecodeError:
                logger.error("Failed to parse message as JSON")
                
    async def create_offer(self) -> RTCSessionDescription:
        """Create an offer for establishing a WebRTC connection."""
        if not self.peer_connection:
            await self.create_peer_connection()
            
        self.data_channel = self.peer_connection.createDataChannel("memory-share")
        self._setup_data_channel(self.data_channel)
        
        offer = await self.peer_connection.createOffer()
        await self.peer_connection.setLocalDescription(offer)
        return offer
        
    async def handle_answer(self, answer: RTCSessionDescription):
        """Handle the received answer to our offer."""
        if self.peer_connection:
            await self.peer_connection.setRemoteDescription(answer)
            
    async def send_message(self, message_type: str, payload: Dict[str, Any]):
        """Send a message through the data channel."""
        if self.data_channel and self.data_channel.readyState == "open":
            message = json.dumps({
                "type": message_type,
                **payload
            })
            self.data_channel.send(message)
        else:
            logger.error("Data channel not ready for sending messages")
            
    def on_message(self, message_type: str, handler: Callable):
        """Register a message handler for a specific message type."""
        self._message_handlers[message_type] = handler
        
    async def close(self):
        """Close the peer connection and cleanup resources."""
        if self.data_channel:
            self.data_channel.close()
        if self.peer_connection:
            await self.peer_connection.close() 
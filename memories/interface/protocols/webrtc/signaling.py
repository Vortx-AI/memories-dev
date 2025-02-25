"""
WebRTC signaling server implementation for connection establishment.
"""
from typing import Dict, Set, Optional, Callable, Any
import asyncio
import json
import logging
from aiohttp import web
from .connection import WebRTCConnection

logger = logging.getLogger(__name__)

class SignalingServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.peers: Dict[str, WebRTCConnection] = {}
        self.rooms: Dict[str, Set[str]] = {}
        self.app = web.Application()
        self.app.router.add_get("/", self.websocket_handler)
        
    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        peer_id = request.query.get("peer_id")
        room_id = request.query.get("room_id")
        
        if not peer_id or not room_id:
            await ws.close(code=4000, message=b"peer_id and room_id are required")
            return ws
            
        # Create or join room
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(peer_id)
        
        # Create WebRTC connection for this peer
        rtc_connection = WebRTCConnection()
        self.peers[peer_id] = rtc_connection
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.handle_message(peer_id, room_id, data, ws)
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            # Cleanup when connection closes
            if room_id in self.rooms:
                self.rooms[room_id].discard(peer_id)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
            if peer_id in self.peers:
                await self.peers[peer_id].close()
                del self.peers[peer_id]
                
        return ws
        
    async def handle_message(self, peer_id: str, room_id: str, data: Dict[str, Any], ws: web.WebSocketResponse):
        """Handle incoming WebSocket messages."""
        message_type = data.get("type")
        
        if message_type == "offer":
            # Forward offer to other peers in the room
            for other_peer_id in self.rooms[room_id]:
                if other_peer_id != peer_id:
                    await self.send_to_peer(other_peer_id, {
                        "type": "offer",
                        "offer": data["offer"],
                        "peer_id": peer_id
                    })
                    
        elif message_type == "answer":
            # Forward answer to the specified peer
            target_peer_id = data.get("peer_id")
            if target_peer_id in self.peers:
                await self.send_to_peer(target_peer_id, {
                    "type": "answer",
                    "answer": data["answer"],
                    "peer_id": peer_id
                })
                
        elif message_type == "ice-candidate":
            # Forward ICE candidate to the specified peer
            target_peer_id = data.get("peer_id")
            if target_peer_id in self.peers:
                await self.send_to_peer(target_peer_id, {
                    "type": "ice-candidate",
                    "candidate": data["candidate"],
                    "peer_id": peer_id
                })
                
    async def send_to_peer(self, peer_id: str, message: Dict[str, Any]):
        """Send a message to a specific peer."""
        if peer_id in self.peers:
            ws = self.peers[peer_id]
            await ws.send_json(message)
            
    async def start(self):
        """Start the signaling server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Signaling server started on ws://{self.host}:{self.port}")
        
    @classmethod
    async def create(cls, host: str = "0.0.0.0", port: int = 8765):
        """Create and start a new signaling server."""
        server = cls(host, port)
        await server.start()
        return server 
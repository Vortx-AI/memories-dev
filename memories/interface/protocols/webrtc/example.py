"""
Example usage of WebRTC implementation showing peer-to-peer communication.
"""
import asyncio
import json
import logging
from typing import Optional
import websockets
from .connection import WebRTCConnection
from .signaling import SignalingServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_client(peer_id: str, room_id: str, ws_url: str) -> None:
    """Run a WebRTC client that connects to the signaling server."""
    # Create WebRTC connection
    connection = WebRTCConnection()
    
    # Set up message handler for received messages
    @connection.on_message("chat")
    async def handle_chat(data):
        logger.info(f"Received chat message: {data.get('message')}")
    
    # Connect to signaling server
    async with websockets.connect(f"{ws_url}?peer_id={peer_id}&room_id={room_id}") as ws:
        logger.info(f"Connected to signaling server as peer {peer_id}")
        
        # Handle signaling messages
        async def handle_signaling():
            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)
                    
                    if data["type"] == "offer":
                        # Handle incoming offer
                        await connection.peer_connection.setRemoteDescription(data["offer"])
                        answer = await connection.peer_connection.createAnswer()
                        await connection.peer_connection.setLocalDescription(answer)
                        
                        await ws.send(json.dumps({
                            "type": "answer",
                            "answer": answer.sdp,
                            "peer_id": data["peer_id"]
                        }))
                        
                    elif data["type"] == "answer":
                        # Handle incoming answer
                        await connection.handle_answer(data["answer"])
                        
                    elif data["type"] == "ice-candidate":
                        # Handle ICE candidate
                        if connection.peer_connection:
                            await connection.peer_connection.addIceCandidate(data["candidate"])
                            
                except Exception as e:
                    logger.error(f"Error in signaling: {e}")
                    break
        
        # Start signaling handler
        signaling_task = asyncio.create_task(handle_signaling())
        
        # If this is the first peer, create and send offer
        if peer_id == "peer1":
            offer = await connection.create_offer()
            await ws.send(json.dumps({
                "type": "offer",
                "offer": offer.sdp
            }))
        
        # Wait for connection to be established
        while not connection.data_channel or connection.data_channel.readyState != "open":
            await asyncio.sleep(0.1)
            
        # Send a test message
        await connection.send_message("chat", {"message": f"Hello from {peer_id}!"})
        
        # Keep connection alive
        try:
            await signaling_task
        finally:
            await connection.close()

async def main():
    """Run the example with a signaling server and two peers."""
    # Start signaling server
    server = await SignalingServer.create("localhost", 8765)
    logger.info("Signaling server started")
    
    # Create and run two peers
    await asyncio.gather(
        run_client("peer1", "test-room", "ws://localhost:8765"),
        run_client("peer2", "test-room", "ws://localhost:8765")
    )

if __name__ == "__main__":
    asyncio.run(main()) 
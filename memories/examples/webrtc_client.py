"""
WebRTC client example that connects to the signaling server and establishes peer connections.
"""
import asyncio
import json
import logging
import websockets
from memories.interface.protocols.webrtc import WebRTCConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_client(peer_id: str, room_id: str = "test-room"):
    """Run a WebRTC client that connects to the signaling server."""
    # Create WebRTC connection
    connection = WebRTCConnection()
    ws_url = "ws://localhost:8765"
    
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
        
        # If this is peer1, create and send offer
        if peer_id == "peer1":
            offer = await connection.create_offer()
            await ws.send(json.dumps({
                "type": "offer",
                "offer": offer.sdp
            }))
            logger.info("Sent connection offer")
        
        try:
            # Wait for connection to be established
            while not connection.data_channel or connection.data_channel.readyState != "open":
                await asyncio.sleep(0.1)
            
            logger.info("Data channel established!")
            
            # Send a test message every 5 seconds
            while True:
                await connection.send_message("chat", {
                    "message": f"Hello from {peer_id}!"
                })
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("Shutting down client...")
        finally:
            await connection.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python webrtc_client.py <peer_id>")
        print("Example: python webrtc_client.py peer1")
        sys.exit(1)
        
    peer_id = sys.argv[1]
    asyncio.run(run_client(peer_id)) 
"""
Test WebRTC chat client that connects to the signaling server in memories.interface.webrtc.signaling_server
"""

import asyncio
import json
import logging
import websockets
from memories.interface.webrtc import WebRTCConnection
from aiortc import RTCSessionDescription, RTCIceCandidate, RTCConfiguration, RTCIceServer
import sys

# Set up logging to show debug information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def run_chat_client(peer_id: str, room_id: str = "test-room"):
    """Run a WebRTC chat client.
    
    Before running this test, start the signaling server:
    python -m memories.interface.webrtc.signaling_server
    """
    logger.info(f"Starting WebRTC chat client as {peer_id} in room {room_id}")
    
    # Create WebRTC connection
    connection = WebRTCConnection()
    
    # Configure STUN server
    connection.peer_connection.configuration = RTCConfiguration([
        RTCIceServer(urls=["stun:stun.l.google.com:19302"])
    ])
    
    # Construct WebSocket URL with proper query parameters
    ws_url = f"ws://localhost:8765/?peer_id={peer_id}&room_id={room_id}"
    logger.info(f"Connecting to signaling server at {ws_url}")
    
    websocket = None
    
    # Set up ICE connection state change handler
    @connection.peer_connection.on("connectionstatechange")
    async def on_connectionstatechange():
        state = connection.peer_connection.connectionState
        logger.info(f"Connection state changed to: {state}")
        if state == "failed":
            logger.error("WebRTC connection failed")
        
    # Set up ICE gathering state change handler
    @connection.peer_connection.on("icegatheringstatechange")
    async def on_icegatheringstatechange():
        state = connection.peer_connection.iceGatheringState
        logger.info(f"ICE gathering state changed to: {state}")
        
    # Set up ICE candidate handler
    @connection.peer_connection.on("icecandidate")
    async def on_icecandidate(event):
        if event.candidate:
            logger.info(f"New ICE candidate gathered: {event.candidate}")
            # Send the ICE candidate to the other peer
            if websocket and not websocket.closed:
                try:
                    await websocket.send(json.dumps({
                        "type": "ice-candidate",
                        "peer_id": "peer2" if peer_id == "peer1" else "peer1",
                        "candidate": {
                            "candidate": event.candidate.candidate,
                            "sdpMid": event.candidate.sdpMid,
                            "sdpMLineIndex": event.candidate.sdpMLineIndex,
                        }
                    }))
                except Exception as e:
                    logger.error(f"Error sending ICE candidate: {e}", exc_info=True)
    
    # Set up data channel handler
    @connection.peer_connection.on("datachannel")
    def on_datachannel(channel):
        logger.info(f"New data channel: {channel.label}")
        connection.data_channel = channel
        
        @channel.on("open")
        def on_open():
            logger.info("Data channel opened")
        
        @channel.on("close")
        def on_close():
            logger.info("Data channel closed")
            
        @channel.on("error")
        def on_error(error):
            logger.error(f"Data channel error: {error}")
            
        @channel.on("message")
        def on_message(message):
            logger.info(f"Received message: {message}")
    
    # Set up message handler for text messages
    @connection.on_message("text")
    async def handle_text(data):
        message = data["data"]
        sender = data.get("metadata", {}).get("sender", "Unknown")
        logger.info(f"Message from {sender}: {message}")
        # Example: Send a response back
        if message.startswith("Hello"):
            response = f"Hi {sender}! Thanks for your message!"
            logger.info(f"Sending response: {response}")
            await connection.send_message(
                "text",
                response,
                {"sender": peer_id}
            )
    
    # Connect to signaling server
    try:
        websocket = await websockets.connect(ws_url)
        logger.info(f"Connected to signaling server as {peer_id}")
        
        # Handle signaling messages
        async def handle_signaling():
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    logger.info(f"Received signaling message: {data['type']}")
                    logger.debug(f"Message content: {data}")
                    
                    if data["type"] == "offer":
                        # Handle incoming offer
                        logger.info("Setting remote description from offer")
                        await connection.peer_connection.setRemoteDescription(
                            RTCSessionDescription(sdp=data["offer"], type="offer")
                        )
                        
                        logger.info("Creating answer")
                        answer = await connection.peer_connection.createAnswer()
                        
                        logger.info("Setting local description")
                        await connection.peer_connection.setLocalDescription(answer)
                        
                        logger.info("Sending answer")
                        await websocket.send(json.dumps({
                            "type": "answer",
                            "answer": answer.sdp,
                            "peer_id": data["peer_id"]
                        }))
                        
                    elif data["type"] == "answer":
                        # Handle incoming answer
                        logger.info("Setting remote description from answer")
                        await connection.peer_connection.setRemoteDescription(
                            RTCSessionDescription(sdp=data["answer"], type="answer")
                        )
                        
                    elif data["type"] == "ice-candidate":
                        # Handle ICE candidate
                        logger.info(f"Adding ICE candidate: {data['candidate']}")
                        candidate = RTCIceCandidate(
                            sdpMid=data["candidate"].get("sdpMid"),
                            sdpMLineIndex=data["candidate"].get("sdpMLineIndex"),
                            candidate=data["candidate"].get("candidate")
                        )
                        await connection.peer_connection.addIceCandidate(candidate)
                            
                except websockets.exceptions.ConnectionClosed:
                    logger.error("Signaling server connection closed")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in signaling message: {e}")
                except Exception as e:
                    logger.error(f"Error in signaling: {e}", exc_info=True)
                    break
        
        # Start signaling handler
        signaling_task = asyncio.create_task(handle_signaling())
        
        # If this is peer1, create and send offer
        if peer_id == "peer1":
            logger.info("Creating data channel")
            channel = connection.peer_connection.createDataChannel("chat")
            connection.data_channel = channel
            
            @channel.on("open")
            def on_open():
                logger.info("Data channel opened")
            
            @channel.on("close")
            def on_close():
                logger.info("Data channel closed")
            
            @channel.on("error")
            def on_error(error):
                logger.error(f"Data channel error: {error}")
            
            logger.info("Creating offer")
            offer = await connection.create_offer()
            
            logger.info("Setting local description")
            await connection.peer_connection.setLocalDescription(offer)
            
            logger.info("Sending offer to peer2")
            await websocket.send(json.dumps({
                "type": "offer",
                "offer": offer.sdp,
                "peer_id": "peer2"  # Target peer
            }))
        
        try:
            # Wait for connection to be established
            logger.info("Waiting for data channel to open")
            timeout = 60  # 60 seconds timeout
            start_time = asyncio.get_event_loop().time()
            
            while True:
                if connection.data_channel and connection.data_channel.readyState == "open":
                    break
                
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError("Data channel failed to open within timeout")
                
                if websocket.closed:
                    raise ConnectionError("WebSocket connection closed")
                
                logger.debug(
                    f"Status - Data channel: {connection.data_channel.readyState if connection.data_channel else 'No channel'}, "
                    f"Connection: {connection.peer_connection.connectionState}, "
                    f"ICE: {connection.peer_connection.iceConnectionState}, "
                    f"Gathering: {connection.peer_connection.iceGatheringState}"
                )
                await asyncio.sleep(1)
            
            logger.info("Chat connection established!")
            
            # Example: Send a greeting message
            greeting = f"Hello from {peer_id}!"
            logger.info(f"Sending greeting: {greeting}")
            await connection.send_message(
                "text",
                greeting,
                {"sender": peer_id}
            )
            
            # Keep the connection alive and allow user input
            while True:
                message = input("Enter message (or 'quit' to exit): ")
                if message.lower() == 'quit':
                    break
                    
                await connection.send_message(
                    "text",
                    message,
                    {"sender": peer_id}
                )
                
        except TimeoutError as e:
            logger.error(f"Connection timeout: {e}")
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except KeyboardInterrupt:
            logger.info("Chat client stopped by user")
        except Exception as e:
            logger.error(f"Error in chat client: {e}", exc_info=True)
        finally:
            logger.info("Closing connection")
            await connection.close()
            signaling_task.cancel()
            if websocket and not websocket.closed:
                await websocket.close()

    except Exception as e:
        logger.error(f"Failed to connect to signaling server: {e}", exc_info=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WebRTC Chat Client")
    parser.add_argument("peer_id", help="Your peer ID (e.g., peer1 or peer2)")
    parser.add_argument("--room", default="test-room", help="Room ID for the chat")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_chat_client(args.peer_id, args.room))
    except KeyboardInterrupt:
        logger.info("Exiting...") 
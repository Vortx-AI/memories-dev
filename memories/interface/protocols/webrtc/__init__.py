"""
WebRTC protocol implementation for peer-to-peer communication.
"""
from .connection import WebRTCConnection
from .signaling import SignalingServer

# Default configuration
DEFAULT_CONFIG = {
    "ice_servers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        # Add TURN servers here if needed
    ],
    "signaling": {
        "host": "0.0.0.0",
        "port": 8765
    }
}

__all__ = ["WebRTCConnection", "SignalingServer", "DEFAULT_CONFIG"] 
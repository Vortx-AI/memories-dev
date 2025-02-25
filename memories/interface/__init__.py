"""
Earth Memory Layer Interface Package
Provides various interfaces for interacting with the Earth Memory Layer system.
"""

from typing import Dict, Any

__version__ = "0.1.0"

# Import core interfaces
from .protocols import BaseProtocol
from .software import APIInterface
from .web3 import Web3Interface
from .agents import AgentInterface
from .physical import PhysicalInterface

__all__ = [
    'BaseProtocol',
    'APIInterface',
    'Web3Interface',
    'AgentInterface',
    'PhysicalInterface'
] 
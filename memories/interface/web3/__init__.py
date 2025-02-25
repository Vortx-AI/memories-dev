"""
Web3 interfaces for Earth Memory Layer.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from web3 import Web3
from eth_typing import Address

class Web3Interface(ABC):
    """Base Web3 interface for Earth Memory Layer."""
    
    def __init__(self, provider_url: str):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self._setup_contracts()
    
    @abstractmethod
    def _setup_contracts(self):
        """Setup smart contracts."""
        pass
    
    @abstractmethod
    async def store_memory_hash(self, memory_id: str, memory_hash: str) -> str:
        """Store memory hash on blockchain."""
        pass
    
    @abstractmethod
    async def verify_memory_hash(self, memory_id: str, memory_hash: str) -> bool:
        """Verify memory hash from blockchain."""
        pass
    
    @abstractmethod
    async def get_memory_history(self, memory_id: str) -> list:
        """Get memory modification history from blockchain."""
        pass
    
    @abstractmethod
    async def grant_access(self, memory_id: str, address: Address) -> bool:
        """Grant access to memory for an address."""
        pass
    
    @abstractmethod
    async def revoke_access(self, memory_id: str, address: Address) -> bool:
        """Revoke access to memory for an address."""
        pass

__all__ = ['Web3Interface'] 
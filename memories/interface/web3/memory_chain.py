"""
Web3 implementation for Earth Memory Layer.
"""

from typing import Dict, Any, List
from eth_typing import Address
from web3 import Web3
from web3.contract import Contract
import json
from memories.core.memory import MemoryStore
from memories.config import Config
from memories.core.utils import calculate_memory_hash
from . import Web3Interface

class MemoryChain(Web3Interface):
    """Blockchain implementation for Earth Memory Layer."""
    
    def __init__(self, provider_url: str, contract_address: str, memory_store: MemoryStore = None):
        """Initialize the blockchain interface.
        
        Args:
            provider_url: Web3 provider URL
            contract_address: Address of deployed memory contract
            memory_store: Optional MemoryStore instance
        """
        super().__init__(provider_url)
        self.contract_address = contract_address
        
        if memory_store is None:
            config = Config(
                storage_path="./data",
                hot_memory_size=50,
                warm_memory_size=200,
                cold_memory_size=1000
            )
            self.memory_store = MemoryStore(config)
        else:
            self.memory_store = memory_store
    
    def _setup_contracts(self):
        """Setup smart contracts."""
        # Load contract ABI
        with open("contracts/Memory.json") as f:
            contract_json = json.load(f)
        
        # Create contract instance
        self.contract = self.web3.eth.contract(
            address=self.contract_address,
            abi=contract_json["abi"]
        )
    
    async def store_memory_hash(self, memory_id: str, memory_hash: str) -> str:
        """Store memory hash on blockchain.
        
        Args:
            memory_id: Memory ID
            memory_hash: Hash of memory data
            
        Returns:
            Transaction hash
        """
        # Get memory data
        memory = self.memory_store.retrieve({"id": memory_id}, memory_type="warm")
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")
        
        # Calculate hash if not provided
        if not memory_hash:
            memory_hash = calculate_memory_hash(memory)
        
        # Store hash on blockchain
        tx_hash = await self.contract.functions.storeMemoryHash(
            memory_id,
            memory_hash
        ).transact()
        
        return tx_hash.hex()
    
    async def verify_memory_hash(self, memory_id: str, memory_hash: str) -> bool:
        """Verify memory hash from blockchain.
        
        Args:
            memory_id: Memory ID
            memory_hash: Hash to verify
            
        Returns:
            True if hash matches
        """
        stored_hash = await self.contract.functions.getMemoryHash(memory_id).call()
        return stored_hash == memory_hash
    
    async def get_memory_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get memory modification history from blockchain.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            List of historical changes
        """
        events = await self.contract.events.MemoryModified.get_logs(
            fromBlock=0,
            argument_filters={"memoryId": memory_id}
        )
        
        return [
            {
                "timestamp": self.web3.eth.get_block(event["blockNumber"])["timestamp"],
                "hash": event["args"]["newHash"],
                "modifier": event["args"]["modifier"]
            }
            for event in events
        ]
    
    async def grant_access(self, memory_id: str, address: Address) -> bool:
        """Grant access to memory for an address.
        
        Args:
            memory_id: Memory ID
            address: Ethereum address to grant access to
            
        Returns:
            True if access was granted
        """
        tx_hash = await self.contract.functions.grantAccess(
            memory_id,
            address
        ).transact()
        
        receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt["status"] == 1
    
    async def revoke_access(self, memory_id: str, address: Address) -> bool:
        """Revoke access to memory for an address.
        
        Args:
            memory_id: Memory ID
            address: Ethereum address to revoke access from
            
        Returns:
            True if access was revoked
        """
        tx_hash = await self.contract.functions.revokeAccess(
            memory_id,
            address
        ).transact()
        
        receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt["status"] == 1 
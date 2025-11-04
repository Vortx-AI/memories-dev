"""
Simple, dependency-free memory store for basic AI fact verification.
Perfect for getting started with memories-dev concepts.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path


class SimpleMemoryStore:
    """
    A lightweight memory store that works without any external dependencies.
    
    This provides the core memory verification concepts shown in README examples
    without requiring DuckDB, FAISS, or other heavy dependencies.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize simple memory store.
        
        Args:
            storage_path: Optional path to persist data (uses in-memory if None)
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.memory_tiers = {
            "hot": {},      # Frequently accessed facts
            "warm": {},     # Regularly accessed facts  
            "cold": {},     # Infrequently accessed facts
        }
        
        # Load existing data if storage path provided
        if self.storage_path and self.storage_path.exists():
            self._load_from_disk()
    
    def store(self, key: str, data: Any, tier: str = "hot") -> bool:
        """Store data in specified memory tier.
        
        Args:
            key: Unique identifier for the data
            data: Data to store (must be JSON serializable)
            tier: Memory tier ("hot", "warm", "cold")
            
        Returns:
            bool: True if stored successfully
        """
        if tier not in self.memory_tiers:
            raise ValueError(f"Invalid tier '{tier}'. Must be one of: {list(self.memory_tiers.keys())}")
        
        # Add metadata
        stored_data = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "tier": tier,
            "access_count": 0
        }
        
        self.memory_tiers[tier][key] = stored_data
        
        # Persist if storage path provided
        if self.storage_path:
            self._save_to_disk()
        
        return True
    
    def retrieve(self, key: str, tier: Optional[str] = None) -> Any:
        """Retrieve data by key.
        
        Args:
            key: Data identifier
            tier: Specific tier to search (searches all if None)
            
        Returns:
            Stored data or None if not found
        """
        tiers_to_search = [tier] if tier else ["hot", "warm", "cold"]
        
        for search_tier in tiers_to_search:
            if key in self.memory_tiers[search_tier]:
                stored_item = self.memory_tiers[search_tier][key]
                # Update access count
                stored_item["access_count"] += 1
                return stored_item["data"]
        
        return None
    
    def verify_fact(self, claim: str, fact_key: str) -> tuple[bool, Any]:
        """Verify a claim against stored facts.
        
        Args:
            claim: Text claim to verify
            fact_key: Key of stored fact to check against
            
        Returns:
            Tuple of (is_verified, stored_fact)
        """
        stored_fact = self.retrieve(fact_key)
        
        if stored_fact is None:
            return False, None
        
        claim_lower = claim.lower()
        
        # Simple string matching verification
        if isinstance(stored_fact, dict):
            # Check if any value in dict matches claim
            for key, value in stored_fact.items():
                if isinstance(value, str):
                    # Look for the subject (key without suffix) in the claim
                    subject = key.replace("_color", "").replace("_", " ")
                    if subject in claim_lower and value.lower() in claim_lower:
                        return True, stored_fact
        elif isinstance(stored_fact, str):
            # Direct string comparison
            if stored_fact.lower() in claim_lower:
                return True, stored_fact
        
        return False, stored_fact
    
    def detect_hallucination(self, claim: str, fact_keys: list[str]) -> Dict[str, Any]:
        """Detect potential hallucinations by checking claim against multiple facts.
        
        Args:
            claim: Claim to verify
            fact_keys: List of fact keys to check against
            
        Returns:
            Dict with verification results
        """
        results = {
            "claim": claim,
            "is_verified": False,
            "corrections": [],
            "confidence": 0.0
        }
        
        verified_count = 0
        
        for fact_key in fact_keys:
            is_verified, stored_fact = self.verify_fact(claim, fact_key)
            
            if is_verified:
                verified_count += 1
            else:
                if stored_fact:
                    results["corrections"].append({
                        "fact_key": fact_key,
                        "stored_fact": stored_fact
                    })
        
        if fact_keys:
            results["confidence"] = verified_count / len(fact_keys)
            results["is_verified"] = results["confidence"] > 0.5
        
        return results
    
    def list_facts(self, tier: Optional[str] = None) -> Dict[str, Any]:
        """List all stored facts.
        
        Args:
            tier: Specific tier to list (all tiers if None)
            
        Returns:
            Dictionary of all facts
        """
        if tier:
            return {k: v["data"] for k, v in self.memory_tiers[tier].items()}
        
        all_facts = {}
        for tier_name, tier_data in self.memory_tiers.items():
            for key, stored_item in tier_data.items():
                all_facts[f"{tier_name}:{key}"] = stored_item["data"]
        
        return all_facts
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics.
        
        Returns:
            Dict with statistics about stored data
        """
        stats = {
            "total_items": 0,
            "tiers": {},
            "most_accessed": None,
            "storage_path": str(self.storage_path) if self.storage_path else "in-memory"
        }
        
        max_access_count = 0
        most_accessed_key = None
        
        for tier_name, tier_data in self.memory_tiers.items():
            tier_stats = {
                "count": len(tier_data),
                "keys": list(tier_data.keys())
            }
            stats["tiers"][tier_name] = tier_stats
            stats["total_items"] += len(tier_data)
            
            # Track most accessed item
            for key, stored_item in tier_data.items():
                if stored_item["access_count"] > max_access_count:
                    max_access_count = stored_item["access_count"]
                    most_accessed_key = f"{tier_name}:{key}"
        
        stats["most_accessed"] = {
            "key": most_accessed_key,
            "access_count": max_access_count
        } if most_accessed_key else None
        
        return stats
    
    def _save_to_disk(self):
        """Save memory store to disk."""
        if not self.storage_path:
            return
        
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.storage_path, 'w') as f:
            json.dump(self.memory_tiers, f, indent=2)
    
    def _load_from_disk(self):
        """Load memory store from disk."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                self.memory_tiers = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or missing, start fresh
            self.memory_tiers = {"hot": {}, "warm": {}, "cold": {}}


class SimpleConfig:
    """Simple configuration class for BasicMemoryStore."""
    
    def __init__(self, storage_path: str = "./memory_data.json"):
        self.storage_path = storage_path


# Convenience functions for README examples
def create_memory_store(storage_path: Optional[str] = None) -> SimpleMemoryStore:
    """Create a simple memory store instance."""
    return SimpleMemoryStore(storage_path)


def verify_ai_response(claim: str, memory_store: SimpleMemoryStore, fact_keys: list[str]) -> Dict[str, Any]:
    """Verify an AI response against stored facts.
    
    Args:
        claim: AI-generated claim to verify
        memory_store: Memory store instance
        fact_keys: Keys of facts to check against
        
    Returns:
        Verification results
    """
    return memory_store.detect_hallucination(claim, fact_keys)
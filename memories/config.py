"""
Configuration for the memories system.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Config:
    """Configuration for the memories system."""
    
    storage_path: str
    hot_memory_size: int
    warm_memory_size: int
    cold_memory_size: int
    redis_url: Optional[str] = "redis://localhost:6379"
    redis_db: Optional[int] = 0
    
    def __post_init__(self):
        """Validate and process configuration after initialization."""
        # Convert storage path to Path object
        self.storage_path = Path(self.storage_path)
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Validate memory sizes
        if self.hot_memory_size <= 0:
            raise ValueError("hot_memory_size must be positive")
        if self.warm_memory_size <= 0:
            raise ValueError("warm_memory_size must be positive")
        if self.cold_memory_size <= 0:
            raise ValueError("cold_memory_size must be positive")
        
        # Validate memory size relationships
        if self.hot_memory_size > self.warm_memory_size:
            raise ValueError("hot_memory_size must be less than or equal to warm_memory_size")
        if self.warm_memory_size > self.cold_memory_size:
            raise ValueError("warm_memory_size must be less than or equal to cold_memory_size") 
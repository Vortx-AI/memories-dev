"""
Utility functions for Earth Memory Layer interfaces.
"""

import logging
from typing import Any, Dict, Optional
import json
import hashlib
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def calculate_memory_hash(data: Dict[str, Any]) -> str:
    """Calculate SHA-256 hash of memory data."""
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()

def validate_memory_data(data: Dict[str, Any]) -> bool:
    """Validate memory data structure."""
    required_fields = ['id', 'content', 'timestamp', 'metadata']
    return all(field in data for field in required_fields)

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format timestamp in ISO format."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()

def parse_config(config_path: str) -> Dict[str, Any]:
    """Parse configuration file."""
    with open(config_path, 'r') as f:
        return json.load(f)

__all__ = [
    'setup_logging',
    'calculate_memory_hash',
    'validate_memory_data',
    'format_timestamp',
    'parse_config'
] 
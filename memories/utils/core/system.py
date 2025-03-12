"""
System utilities for memories-dev.
"""

from dataclasses import dataclass
from typing import List, Optional
import logging
import torch
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

from memories.config import get_config

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """Status of the system check."""
    ok: bool
    messages: List[str]
    warnings: List[str]
    errors: List[str]

def system_check() -> SystemStatus:
    """Run a system check to verify the installation and configuration.
    
    Returns:
        SystemStatus: Object containing check results
    """
    messages = []
    warnings = []
    errors = []
    ok = True
    
    try:
        # Check configuration
        config = get_config()
        messages.append("✓ Configuration system initialized")
        
        # Check storage
        if config.storage_config:
            messages.append(f"✓ Storage configured ({config.storage_config.storage_type})")
        else:
            warnings.append("⚠ Storage not configured")
            
        # Check ML backends
        if config.backend == "pytorch":
            messages.append("✓ Using PyTorch backend")
            if torch.cuda.is_available():
                messages.append(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
            else:
                warnings.append("⚠ GPU not available for PyTorch - using CPU")
        elif config.backend == "tensorflow":
            if TENSORFLOW_AVAILABLE:
                messages.append("✓ Using TensorFlow backend")
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    messages.append(f"✓ {len(gpus)} GPU(s) available for TensorFlow")
                else:
                    warnings.append("⚠ GPU not available for TensorFlow - using CPU")
            else:
                errors.append("✗ TensorFlow backend selected but not installed")
                ok = False
                
        # Check optional dependencies
        try:
            import cudf
            messages.append("✓ GPU-accelerated DataFrames available (cudf)")
        except ImportError:
            warnings.append("⚠ cudf not available - GPU acceleration for DataFrames disabled")
            
        try:
            import cuspatial
            messages.append("✓ GPU-accelerated spatial operations available (cuspatial)")
        except ImportError:
            warnings.append("⚠ cuspatial not available - GPU acceleration for spatial operations disabled")
            
        # Check memory system
        try:
            import duckdb
            messages.append("✓ DuckDB client available")
            # Try creating an in-memory DuckDB connection
            con = duckdb.connect(database=':memory:')
            con.execute("SELECT 1")
            messages.append("✓ DuckDB in-memory database working correctly")
            con.close()
        except ImportError:
            errors.append("✗ DuckDB not installed - memory system will not function correctly")
        except Exception as e:
            errors.append(f"✗ DuckDB error: {str(e)}")
            
    except Exception as e:
        errors.append(f"✗ Unexpected error during system check: {str(e)}")
        ok = False
        
    return SystemStatus(
        ok=ok and not errors,
        messages=messages,
        warnings=warnings,
        errors=errors
    ) 
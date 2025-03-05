# src/config.py
"""
Configuration management for the Memories framework.
"""

import os
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv
from typing import Dict, Any, Optional

DEFAULT_CONFIG = {
    'memory': {
        'base_path': './data/memory',
        'red_hot': {
            'path': 'red_hot',
            'max_size': 1000000,  # 1M vectors
            'vector_dim': 384,    # Default for all-MiniLM-L6-v2
            'gpu_id': 0,
            'force_cpu': True,    # Default to CPU for stability
            'index_type': 'Flat'  # Simple Flat index
        },
        'hot': {
            'path': 'hot',
            'max_size': 104857600,  # 100MB
            'redis_url': 'redis://localhost:6379',
            'redis_db': 0
        },
        'warm': {
            'path': 'warm',
            'max_size': 1073741824,  # 1GB
            'duckdb': {
                'memory_limit': '8GB',
                'threads': 4,
                'config': {
                    'enable_progress_bar': True,
                    'enable_object_cache': True
                }
            }
        },
        'cold': {
            'path': 'cold',
            'max_size': 10737418240,  # 10GB
            'duckdb': {
                'memory_limit': '8GB',
                'threads': 4,
                'config': {
                    'enable_progress_bar': True,
                    'enable_object_cache': True
                }
            }
        },
        'glacier': {
            'path': 'glacier',
            'max_size': 107374182400,  # 100GB
            'remote_storage': {
                'type': 'local',
                'path': './data/glacier'
            }
        }
    }
}

class Config:
    """Configuration manager for the Memories framework."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Optional path to config file
        """
        # Load environment variables
        load_dotenv()
        
        # Set up project paths
        self.project_root = os.getenv("PROJECT_ROOT") or os.path.abspath(os.getcwd())
        if self.project_root not in sys.path:
            sys.path.append(self.project_root)
            print(f"Added {self.project_root} to Python path")
            
        # Load configuration
        self.config_path = config_path or os.path.join(self.project_root, 'config/db_config.yml')
        self.config = self._load_config()
        self._setup_directories()
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        config = DEFAULT_CONFIG.copy()
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._deep_update(config, file_config)
                    
            # Convert relative paths to absolute
            for section in ['memory']:
                if section in config:
                    for tier in ['red_hot', 'hot', 'warm', 'cold', 'glacier']:
                        if tier in config[section]:
                            path = config[section][tier].get('path')
                            if path and isinstance(path, str) and path.startswith('./'):
                                config[section][tier]['path'] = os.path.abspath(
                                    os.path.join(self.project_root, path.lstrip('./'))
                                )
                            
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return config
            
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Recursively update a dictionary."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def _setup_directories(self):
        """Create necessary directories."""
        for section in ['memory']:
            if section in self.config:
                for tier in ['red_hot', 'hot', 'warm', 'cold', 'glacier']:
                    if tier in self.config[section]:
                        path = self.config[section][tier].get('path')
                        if path:
                            os.makedirs(path, exist_ok=True)
                            
    def __getitem__(self, key: str) -> Any:
        """Make config subscriptable."""
        return self.config[key]
        
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow setting config values."""
        self.config[key] = value
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with default."""
        return self.config.get(key, default)

    @property
    def storage_path(self) -> Path:
        """Get the database storage path."""
        return Path(self.config['database']['path'])
        
    @property
    def redis_url(self) -> str:
        """Get the Redis URL."""
        return self.config['redis']['url']
        
    @property
    def redis_db(self) -> int:
        """Get the Redis database number."""
        return self.config['redis']['db']
        
    @property
    def hot_memory_size(self) -> int:
        """Get the hot memory size."""
        return self.config['memory']['hot']['max_size']
        
    @property
    def red_hot_memory_size(self) -> int:
        """Get the red hot memory size."""
        return self.config['memory']['red_hot']['max_size']
        
    @property
    def vector_dim(self) -> int:
        """Get the vector dimension for FAISS."""
        return self.config['memory']['red_hot']['vector_dim']
        
    @property
    def gpu_id(self) -> int:
        """Get the GPU device ID."""
        return self.config['memory']['red_hot']['gpu_id']
        
    @property
    def faiss_index_type(self) -> str:
        """Get the FAISS index type."""
        return self.config['memory']['red_hot']['index_type']
        
    @property
    def warm_memory_size(self) -> int:
        """Get the warm memory size."""
        return self.config['memory']['warm']['max_size']
        
    @property
    def cold_memory_size(self) -> int:
        """Get the cold memory size."""
        return self.config['memory']['cold']['max_size']
        
    def get_database_path(self) -> str:
        """Get the full database path."""
        return os.path.join(
            self.config['database']['path'],
            self.config['database']['name']
        )
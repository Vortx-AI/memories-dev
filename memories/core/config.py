# src/config.py
"""
Configuration management for the Memories framework.
"""

import os
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

class Config:
    """Configuration manager for the Memories framework."""
    
    def __init__(self, config_path: str = None):
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
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Convert relative paths to absolute
            for section in ['database', 'data']:
                if section in config:
                    for key, value in config[section].items():
                        if isinstance(value, str) and value.startswith('./'):
                            config[section][key] = os.path.abspath(
                                os.path.join(self.project_root, value.lstrip('./'))
                            )
                            
            return config
        except Exception as e:
            print(f"Error loading config from {self.config_path}: {e}")
            return {
                'database': {
                    'path': os.path.join(self.project_root, 'examples/data/db'),
                    'name': 'location_ambience.db'
                },
                'data': {
                    'raw_path': os.path.join(self.project_root, 'examples/data/raw'),
                    'processed_path': os.path.join(self.project_root, 'examples/data/processed'),
                    'overture_path': os.path.join(self.project_root, 'examples/data/overture'),
                    'satellite_path': os.path.join(self.project_root, 'examples/data/satellite'),
                    'location_data_path': os.path.join(self.project_root, 'examples/data/location_data')
                },
                'memory': {
                    'red_hot_size': 1000000,  # 1M vectors for GPU FAISS
                    'hot_size': 50,
                    'warm_size': 200,
                    'cold_size': 1000,
                    'vector_dim': 384,  # Default vector dimension
                    'gpu_id': 0,  # Default GPU device
                    'faiss_index_type': 'IVFFlat',  # Default FAISS index type
                    'hot': {
                        'duckdb': {
                            'memory_limit': '2GB',
                            'threads': 2
                        }
                    },
                    'warm': {
                        'duckdb': {
                            'memory_limit': '8GB',
                            'threads': 4
                        }
                    }
                }
            }
            
    def _setup_directories(self):
        """Create necessary directories if they don't exist."""
        for section in ['database', 'data']:
            if section in self.config:
                for path in self.config[section].values():
                    if isinstance(path, str) and not path.endswith('.db'):
                        Path(path).mkdir(parents=True, exist_ok=True)
                        
    @property
    def storage_path(self) -> Path:
        """Get the database storage path."""
        return Path(self.config['database']['path'])
        
    @property
    def hot_duckdb_config(self) -> dict:
        """Get the hot memory DuckDB configuration."""
        return self.config['memory'].get('hot', {}).get('duckdb', {
            'memory_limit': '2GB',
            'threads': 2
        })
        
    @property
    def warm_duckdb_config(self) -> dict:
        """Get the warm memory DuckDB configuration."""
        return self.config['memory'].get('warm', {}).get('duckdb', {
            'memory_limit': '8GB',
            'threads': 4
        })
        
    @property
    def hot_memory_size(self) -> int:
        """Get the hot memory size."""
        return self.config['memory']['hot_size']
        
    @property
    def red_hot_memory_size(self) -> int:
        """Get the red hot memory size."""
        return self.config['memory']['red_hot_size']
        
    @property
    def vector_dim(self) -> int:
        """Get the vector dimension for FAISS."""
        return self.config['memory']['vector_dim']
        
    @property
    def gpu_id(self) -> int:
        """Get the GPU device ID."""
        return self.config['memory']['gpu_id']
        
    @property
    def faiss_index_type(self) -> str:
        """Get the FAISS index type."""
        return self.config['memory']['faiss_index_type']
        
    @property
    def warm_memory_size(self) -> int:
        """Get the warm memory size."""
        return self.config['memory']['warm_size']
        
    @property
    def cold_memory_size(self) -> int:
        """Get the cold memory size."""
        return self.config['memory']['cold_size']
        
    def get_database_path(self) -> str:
        """Get the full database path."""
        return os.path.join(
            self.config['database']['path'],
            self.config['database']['name']
        )
        
    def get_path(self, config_key: str, default_filename: str = None) -> str:
        """Get a path from the configuration, or use a default relative to the memory base path.
        
        Args:
            config_key: The key in the config to look for
            default_filename: Default filename to use if the key is not found
            
        Returns:
            Resolved path as a string
        """
        # Check if the key exists in memory section
        if 'memory' in self.config and config_key in self.config['memory']:
            return self.config['memory'][config_key]
            
        # If not found, use the default filename relative to base_path
        if default_filename and 'memory' in self.config and 'base_path' in self.config['memory']:
            return os.path.join(self.config['memory']['base_path'], default_filename)
            
        # Last resort fallback
        return os.path.join(self.project_root, 'data', 'memory', default_filename or '')
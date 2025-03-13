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
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_directories()
        
    def _load_config(self) -> dict:
        """Load configuration from file or use defaults."""
        # Start with hardcoded defaults
        config = self._get_hardcoded_defaults()
        
        # If config_path is provided, try to load from there
        if self.config_path:
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Deep merge user_config into config
                    self._deep_update(config, user_config)
                print(f"Loaded user configuration from {self.config_path}")
            except Exception as e:
                print(f"Error loading user configuration from {self.config_path}: {e}")
                print("Using default configuration")
        else:
            # Try to load from standard locations in order of priority
            standard_paths = [
                os.path.join(self.project_root, 'config', 'default_config.yml'),
                os.path.join(os.getcwd(), 'config', 'default_config.yml'),
                os.path.join(os.path.dirname(__file__), 'glacier', 'default_config.yml'),
                os.path.join(self.project_root, 'config', 'db_config.yml'),
                os.path.join(os.getcwd(), 'config', 'db_config.yml')
            ]
            
            config_loaded = False
            for path in standard_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r') as f:
                            user_config = yaml.safe_load(f)
                            # Deep merge user_config into config
                            self._deep_update(config, user_config)
                        print(f"Loaded configuration from {path}")
                        config_loaded = True
                        break
                    except Exception as e:
                        print(f"Error loading configuration from {path}: {e}")
            
            # If no config file was found, use hardcoded defaults
            if not config_loaded:
                print("No configuration file found. Using default configuration.")
        
        # Convert relative paths to absolute
        for section in ['database', 'data']:
            if section in config:
                for key, value in config[section].items():
                    if isinstance(value, str) and value.startswith('./'):
                        config[section][key] = os.path.abspath(
                            os.path.join(self.project_root, value.lstrip('./'))
                        )
                        
        return config
    
    def _deep_update(self, base_dict, update_dict):
        """Recursively update a dictionary with another dictionary."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _get_hardcoded_defaults(self) -> dict:
        """Get hardcoded default configuration as a last resort."""
        return {
            'database': {
                'path': os.path.join(self.project_root, 'data', 'db'),
                'name': 'memories.db'
            },
            'data': {
                'storage': os.path.join(self.project_root, 'data', 'storage'),
                'models': os.path.join(self.project_root, 'data', 'models'),
                'cache': os.path.join(self.project_root, 'data', 'cache'),
                'raw_path': os.path.join(self.project_root, 'data', 'raw'),
                'processed_path': os.path.join(self.project_root, 'data', 'processed')
            },
            'memory': {
                'base_path': os.path.join(self.project_root, 'data', 'memory'),
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
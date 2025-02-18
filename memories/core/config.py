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
        self.config_path = config_path or os.path.join(self.project_root, 'examples/config/db_config.yml')
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
                    'hot_size': 50,
                    'warm_size': 200,
                    'cold_size': 1000
                },
                'redis': {
                    'url': 'redis://localhost:6379',
                    'db': 0
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
        return self.config['memory']['hot_size']
        
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

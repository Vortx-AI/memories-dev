# src/config.py
import yaml
from pathlib import Path
import os , sys
from dotenv import load_dotenv
class Config:
     
    load_dotenv()

    # Add the project root to Python path if needed
    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        # If PROJECT_ROOT is not set, try to find it relative to the notebook
        project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

    #print(f"Using project root: {project_root}")

    if project_root not in sys.path:
        sys.path.append(project_root)
        print(f"Added {project_root} to Python path")

    config_x = project_root + '/config/db_config.yml'

    def __init__(self, config_path: str = config_x):
        self.config = self._load_config(config_path)
        self._setup_directories()

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.config['data']['raw_path'],
            #self.config['data']['processed_path'],
            'logs'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def get_database_path(self) -> str:
        return os.path.join(
            self.config['database']['path'],
            self.config['database']['name']
        )

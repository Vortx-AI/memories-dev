# src/database.py
import duckdb
import yaml
from pathlib import Path
import logging
from typing import List, Dict, Any
import os,sys
from dotenv import load_dotenv

class DuckDBHandler:
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
        self.con = None
        self._setup_logging()
        self.setup_database()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename='logs/database.log',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_database(self):
        """Initialize database connection"""
        try:
            db_path = os.path.join(
                self.config['database']['path'],
                self.config['database']['name']
            )
            self.con = duckdb.connect(db_path)
            self.logger.info(f"Connected to database: {db_path}")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def load_parquet_files(self, table_name: str):
        """Load all parquet files from raw directory into table"""
        try:
            raw_path = Path(self.config['data']['raw_path'])
            parquet_files = list(raw_path.glob('*.parquet'))

            if not parquet_files:
                raise ValueError(f"No parquet files found in {raw_path}")

            # Create table from first file
            self.con.sql(f"""
                CREATE TABLE IF NOT EXISTS {table_name} AS 
                SELECT * FROM parquet_scan('{parquet_files[0]}')
            """)

            # Insert data from remaining files
            for file in parquet_files[1:]:
                self.con.sql(f"""
                    INSERT INTO {table_name}
                    SELECT * FROM parquet_scan('{file}')
                """)

            self.logger.info(f"Loaded {len(parquet_files)} files into table {table_name}")

        except Exception as e:
            self.logger.error(f"Error loading parquet files: {str(e)}")
            raise

    def query(self, sql: str) -> Any:
        """Execute SQL query"""
        try:
            return self.con.sql(sql).df()
        except Exception as e:
            self.logger.error(f"Query error: {str(e)}")
            raise

    def close(self):
        """Close database connection"""
        if self.con:
            self.con.close()
            self.logger.info("Database connection closed")

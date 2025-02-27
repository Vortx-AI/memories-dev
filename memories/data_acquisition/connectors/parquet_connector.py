from pathlib import Path
from typing import Union, List, Optional, Any, Dict
import duckdb
import logging
from glob import glob

class ParquetConnector:
    """Connector for querying Parquet files using DuckDB"""
    
    def __init__(self, path: Union[str, Path], view_name: str = "parquet_view"):
        """Initialize ParquetConnector.
        
        Args:
            path: Path to parquet file or directory containing parquet files
            view_name: Name of the DuckDB view to create (default: "parquet_view")
        """
        self.logger = logging.getLogger(__name__)
        self.path = Path(path)
        self.view_name = view_name
        self.con = duckdb.connect()
        
        # Initialize connection
        self._initialize()
    
    def _initialize(self):
        """Initialize the connection and create view"""
        try:
            # Get all parquet files
            self.parquet_files = self._get_parquet_files()
            if not self.parquet_files:
                raise ValueError(f"No parquet files found at {self.path}")
                
            self.logger.info(f"Found {len(self.parquet_files)} parquet file(s)")
            
            # Create view
            self._create_view()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ParquetConnector: {e}")
            raise
    
    def _get_parquet_files(self) -> List[Path]:
        """Get list of parquet files from path"""
        files = []
        try:
            if self.path.is_file() and self.path.suffix == '.parquet':
                files = [self.path]
            elif self.path.is_dir():
                # Recursively find all parquet files
                files = list(self.path.rglob("*.parquet"))
            
            return files
            
        except Exception as e:
            self.logger.error(f"Error finding parquet files: {e}")
            return []
    
    def _create_view(self):
        """Create DuckDB view from parquet files"""
        try:
            # Create view combining all parquet files
            files_str = ",".join(f"'{str(f)}'" for f in self.parquet_files)
            view_query = f"""
            CREATE OR REPLACE VIEW {self.view_name} AS 
            SELECT * FROM read_parquet([{files_str}])
            """
            
            self.con.execute(view_query)
            self.logger.info(f"Created view '{self.view_name}' from {len(self.parquet_files)} files")
            
            # Get schema information
            self.schema = self.con.execute(f"DESCRIBE {self.view_name}").fetchdf()
            self.logger.debug(f"View schema:\n{self.schema}")
            
        except Exception as e:
            self.logger.error(f"Error creating view: {e}")
            raise
    
    def query(self, query: str) -> Any:
        """Execute a SQL query.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query results as pandas DataFrame
        """
        try:
            self.logger.debug(f"Executing query: {query}")
            result = self.con.execute(query).fetchdf()
            self.logger.debug(f"Query returned {len(result)} rows")
            return result
            
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """Get schema information for the parquet files"""
        try:
            schema_info = {}
            for _, row in self.schema.iterrows():
                schema_info[row['column_name']] = {
                    'type': row['column_type'],
                    'nullable': 'NOT NULL' not in str(row.get('null', ''))
                }
            return schema_info
            
        except Exception as e:
            self.logger.error(f"Error getting schema: {e}")
            return {}
    
    def get_row_count(self) -> int:
        """Get total number of rows in the parquet files"""
        try:
            count = self.query(f"SELECT COUNT(*) as count FROM {self.view_name}")
            return count.iloc[0]['count']
            
        except Exception as e:
            self.logger.error(f"Error getting row count: {e}")
            return 0
    
    def get_sample(self, n: int = 5) -> Any:
        """Get sample rows from the parquet files"""
        try:
            return self.query(f"SELECT * FROM {self.view_name} LIMIT {n}")
            
        except Exception as e:
            self.logger.error(f"Error getting sample: {e}")
            return None
    
    def get_column_names(self) -> List[str]:
        """Get list of column names from the parquet files.
        
        Returns:
            List of column names
        """
        try:
            return list(self.schema['column_name'])
        except Exception as e:
            self.logger.error(f"Error getting column names: {e}")
            return []
    
    def get_columns_with_types(self) -> Dict[str, str]:
        """Get dictionary of column names and their corresponding data types.
        
        Returns:
            Dictionary mapping column names to their data types
        """
        try:
            return dict(zip(self.schema['column_name'], self.schema['column_type']))
        except Exception as e:
            self.logger.error(f"Error getting column names and types: {e}")
            return {}
    
    def close(self):
        """Close the DuckDB connection"""
        try:
            self.con.close()
            self.logger.info("Closed DuckDB connection")
            
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}") 
"""
Data connectors for different data sources.
"""

import logging
from pathlib import Path
from typing import Union, List, Dict, Any, Optional, Literal
from .parquet_connector import ParquetConnector
from ..core.red_hot import RedHotMemory

logger = logging.getLogger(__name__)

ConnectionType = Literal['parquet', 'multi-parquet']  # Add more types as needed

class DataConnector:
    """Generic connector for different data sources that indexes information in FAISS."""
    
    def __init__(
        self,
        red_hot_memory: RedHotMemory,
        vector_encoder: Any,  # This should be your text-to-vector encoder
        connection_type: ConnectionType,
        folder_path: Union[str, Path]
    ):
        """Initialize DataConnector.
        
        Args:
            red_hot_memory: Instance of RedHotMemory for storing information
            vector_encoder: Model/function to encode text into vectors
            connection_type: Type of data connection ('parquet' or 'multi-parquet')
            folder_path: Path to file or directory depending on connection_type
        """
        self.red_hot_memory = red_hot_memory
        self.vector_encoder = vector_encoder
        self.connection_type = connection_type
        self.folder_path = Path(folder_path)
        
        # Initialize appropriate connector based on type
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """Initialize the connection based on the connection type."""
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Path does not exist: {self.folder_path}")
            
        if self.connection_type == 'parquet':
            if not ParquetConnector.validate_parquet_path(self.folder_path):
                raise ValueError(f"Invalid parquet file: {self.folder_path}")
            self._process_parquet_file(self.folder_path)
            
        elif self.connection_type == 'multi-parquet':
            if not self.folder_path.is_dir():
                raise ValueError(f"For connection_type='multi-parquet', path must be a directory: {self.folder_path}")
            self._process_parquet_directory(self.folder_path)
            
        else:
            raise ValueError(f"Unsupported connection type: {self.connection_type}")
    
    def _process_parquet_file(self, file_path: Path) -> None:
        """Process a single parquet file and store its column information.
        
        Args:
            file_path: Path to the parquet file
        """
        try:
            # Get schema info from ParquetConnector
            schema_info = ParquetConnector.get_schema_info(file_path)
            
            # Process each column
            for column in schema_info["columns"]:
                # Create vector embedding for the column name
                column_vector = self.vector_encoder(column["name"])
                
                # Prepare metadata
                metadata = {
                    "file_path": schema_info["file_path"],
                    "data_type": column["data_type"],
                    "is_geometry": column["is_geometry"],
                    "duckdb_query": column["duckdb_query"],
                    "connection_type": self.connection_type
                }
                
                # Store in FAISS
                self.red_hot_memory.store(
                    key=f"column:{self.connection_type}:{file_path.name}:{column['name']}",
                    vector_data=column_vector,
                    metadata=metadata
                )
                
            logger.info(f"Successfully processed parquet file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing parquet file {file_path}: {e}")
            raise
    
    def _process_parquet_directory(self, directory_path: Path) -> None:
        """Process all parquet files in a directory.
        
        Args:
            directory_path: Path to directory containing parquet files
        """
        parquet_files = ParquetConnector.find_parquet_files(directory_path)
        if not parquet_files:
            logger.warning(f"No parquet files found in {directory_path}")
            return
            
        for file_path in parquet_files:
            self._process_parquet_file(file_path)
    
    def query_columns(
        self,
        search_text: str,
        k: int = 5,
        geometry_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for columns matching the search text.
        
        Args:
            search_text: Text to search for
            k: Number of results to return
            geometry_only: If True, only return geometry columns
            
        Returns:
            List of matching columns with their metadata
        """
        # Create vector embedding for search text
        query_vector = self.vector_encoder(search_text)
        
        # Prepare metadata filters
        metadata_filter = {}
        if geometry_only:
            metadata_filter["is_geometry"] = True
        
        # Search in FAISS
        results = self.red_hot_memory.search(
            query_vector=query_vector,
            k=k,
            metadata_filter=metadata_filter
        )
        
        return results

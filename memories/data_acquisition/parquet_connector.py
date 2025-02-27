"""
Parquet-specific connector implementation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

class ParquetConnector:
    """Handles parquet-specific operations for data connection."""

    @staticmethod
    def get_schema_info(file_path: Path) -> Dict[str, Any]:
        """Get schema and metadata information from a parquet file.
        
        Args:
            file_path: Path to the parquet file
            
        Returns:
            Dictionary containing schema information and metadata
        """
        try:
            # Read parquet schema
            parquet_file = pq.ParquetFile(file_path)
            schema = parquet_file.schema
            
            # Get geometry columns if any (checking common geometry column names)
            geometry_columns = []
            columns_info = []
            
            for field in schema:
                # Check if it's a geometry column
                is_geometry = any(geom_keyword in field.name.lower() 
                                for geom_keyword in ['geometry', 'geom', 'shape', 'point', 'polygon'])
                if is_geometry:
                    geometry_columns.append(field.name)
                
                # Collect column information
                columns_info.append({
                    "name": field.name,
                    "data_type": str(field.type),
                    "is_geometry": is_geometry,
                    "duckdb_query": f"SELECT {field.name} FROM read_parquet('{file_path}')"
                })
            
            return {
                "columns": columns_info,
                "geometry_columns": geometry_columns,
                "file_path": str(file_path.absolute())
            }
            
        except Exception as e:
            logger.error(f"Error reading parquet file {file_path}: {e}")
            raise

    @staticmethod
    def validate_parquet_path(file_path: Path) -> bool:
        """Validate if the given path is a valid parquet file.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if valid, False otherwise
        """
        return file_path.is_file() and str(file_path).endswith('.parquet')

    @staticmethod
    def find_parquet_files(directory_path: Path) -> List[Path]:
        """Find all parquet files in a directory.
        
        Args:
            directory_path: Directory to search in
            
        Returns:
            List of paths to parquet files
        """
        return list(directory_path.glob("*.parquet")) 
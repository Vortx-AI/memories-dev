import logging
from pathlib import Path
import pandas as pd
import duckdb
import os
from typing import Dict, List, Tuple, Optional
from memories.core.red_hot_memory import RedHotMemory
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

class ColdToRedHot:
    def __init__(self, data_dir: str = None, config_path: str = None):
        """Initialize cold to red-hot transfer manager."""
        self.data_dir = data_dir or os.path.expanduser("~/geo_memories")
        self.red_hot = RedHotMemory(config_path)
        self.con = duckdb.connect(database=':memory:')
        self.con.install_extension("spatial")
        self.con.load_extension("spatial")

    def get_parquet_files(self) -> List[str]:
        """Get all parquet files from cold_metadata."""
        try:
            query = """
                SELECT DISTINCT file_path 
                FROM cold_metadata 
                ORDER BY file_path
            """
            result = self.con.execute(query).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error querying cold_metadata: {e}")
            return []

    def get_file_metadata_from_cold(self, file_path: str) -> Dict:
        """Get file metadata from cold_metadata table."""
        try:
            query = """
                SELECT 
                    file_path,
                    MIN(created_at) as created_at,
                    COUNT(*) as row_count,
                    MIN(source_type) as source_type
                FROM cold_metadata 
                WHERE file_path = ?
                GROUP BY file_path
            """
            result = self.con.execute(query, [file_path]).fetchone()
            if result:
                return {
                    'file_path': result[0],
                    'created_at': result[1],
                    'row_count': result[2],
                    'source_type': result[3]
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting metadata for {file_path}: {e}")
            return {}

    def get_file_schema(self, file_path: str) -> List[Tuple[str, str]]:
        """Get schema information from a parquet file."""
        try:
            parquet_file = pq.ParquetFile(file_path)
            schema = parquet_file.schema
            return [(field.name, str(field.type)) for field in schema]
        except Exception as e:
            logger.error(f"Error reading schema from {file_path}: {e}")
            return []

    def get_column_statistics(self, file_path: str) -> Dict:
        """Get basic statistics for columns in a parquet file."""
        try:
            # Read parquet metadata
            parquet_file = pq.ParquetFile(file_path)
            stats = {}
            
            # Get statistics from parquet metadata if available
            for row_group in parquet_file.metadata.row_groups:
                for column in row_group.columns:
                    col_name = column.path_in_schema
                    if col_name not in stats:
                        stats[col_name] = {}
                    
                    if column.statistics:
                        stats[col_name].update({
                            'null_count': column.statistics.null_count,
                            'distinct_count': column.statistics.distinct_count,
                            'min_value': str(column.statistics.min),
                            'max_value': str(column.statistics.max)
                        })
            
            return stats
        except Exception as e:
            logger.error(f"Error getting column statistics from {file_path}: {e}")
            return {}

    def transfer_schema_to_redhot(self, file_path: str):
        """Transfer schema information from a cold storage file to red-hot memory."""
        try:
            # Get schema
            schema = self.get_file_schema(file_path)
            if not schema:
                return
            
            # Get metadata from cold_metadata
            cold_metadata = self.get_file_metadata_from_cold(file_path)
            
            # Get additional information
            parquet_file = pq.ParquetFile(file_path)
            additional_info = {
                'row_count': cold_metadata.get('row_count', parquet_file.metadata.num_rows),
                'column_stats': self.get_column_statistics(file_path),
                'source_type': cold_metadata.get('source_type'),
                'created_at': cold_metadata.get('created_at')
            }
            
            # Add to red-hot memory
            self.red_hot.add_file_schema(file_path, schema, additional_info)
            logger.info(f"Transferred schema for {file_path} to red-hot memory")
            
        except Exception as e:
            logger.error(f"Error transferring schema for {file_path}: {e}")

    def transfer_all_schemas(self):
        """Transfer schema information for all files in cold_metadata to red-hot memory."""
        files = self.get_parquet_files()
        logger.info(f"Found {len(files)} files in cold_metadata")
        
        for file_path in files:
            self.transfer_schema_to_redhot(file_path)

def main():
    """Main function to run the transfer process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    transfer = ColdToRedHot()
    transfer.transfer_all_schemas()

if __name__ == "__main__":
    main() 
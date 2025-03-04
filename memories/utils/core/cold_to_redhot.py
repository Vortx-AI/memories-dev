import logging
from pathlib import Path
import pandas as pd
import duckdb
import os
from typing import Dict, List, Tuple, Optional
from memories.core.red_hot_memory import RedHotMemory
import pyarrow.parquet as pq
import glob
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class ColdToRedHot:
    def __init__(self, config_path: str = None):
        """Initialize cold to red-hot transfer."""
        # Set up data directory
        self.data_dir = os.path.expanduser("~/geo_memories")
        
        # Set up red-hot storage path
        project_root = Path(__file__).parent.parent.parent.parent
        self.storage_path = os.path.join(project_root, "data", "red_hot")
        
        # Initialize components
        self.red_hot = RedHotMemory(
            storage_path=self.storage_path,
            max_size=1_000_000
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize cold metadata
        self._initialize_cold_metadata()
        
        logger.info(f"Initialized ColdToRedHot with:")
        logger.info(f"  Data directory: {self.data_dir}")
        logger.info(f"  FAISS storage: {self.storage_path}")

    def get_file_schema(self, file_path: str) -> List[Tuple[str, str]]:
        """Get schema information from a parquet file."""
        try:
            parquet_file = pq.ParquetFile(file_path)
            schema = parquet_file.schema_arrow  # Use arrow schema instead
            return [(field.name, field.type) for field in schema]
        except Exception as e:
            logger.error(f"Error reading schema from {file_path}: {e}")
            return []

    def get_column_statistics(self, file_path: str) -> Dict:
        """Get basic statistics for columns in a parquet file."""
        try:
            parquet_file = pq.ParquetFile(file_path)
            stats = {}
            
            # Get statistics from parquet metadata
            metadata = parquet_file.metadata
            for i in range(metadata.num_row_groups):
                row_group = metadata.row_group(i)
                for j in range(row_group.num_columns):
                    column = row_group.column(j)
                    col_name = column.path_in_schema
                    if col_name not in stats:
                        stats[col_name] = {}
                    
                    column_stats = column.statistics
                    if column_stats:
                        stats[col_name].update({
                            'null_count': column_stats.null_count,
                            'distinct_count': column_stats.distinct_count,
                            'min_value': str(column_stats.min) if column_stats.min is not None else None,
                            'max_value': str(column_stats.max) if column_stats.max is not None else None
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
            
            # Convert timestamp to string to avoid conversion issues
            if cold_metadata.get('created_at'):
                cold_metadata['created_at'] = str(cold_metadata['created_at'])
            
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

    def get_file_metadata_from_cold(self, file_path: str) -> Dict:
        """Get file metadata from cold_metadata table."""
        try:
            query = """
                SELECT 
                    file_path,
                    created_at,
                    source_type
                FROM cold_metadata 
                WHERE file_path = ?
                LIMIT 1
            """
            result = self.con.execute(query, [file_path]).fetchone()
            if result:
                return {
                    'file_path': result[0],
                    'created_at': result[1],
                    'source_type': result[2]
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting metadata for {file_path}: {e}")
            return {}

    def _initialize_cold_metadata(self):
        """Initialize cold metadata by scanning parquet files."""
        try:
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
                logger.info(f"Created data directory: {self.data_dir}")
            
            patterns = [
                "**/base/**/*.parquet",
                "**/divisions/**/*.parquet",
                "**/transportation/**/*.parquet"
            ]
            
            self.parquet_files = []
            for pattern in patterns:
                self.parquet_files.extend(
                    glob.glob(os.path.join(self.data_dir, pattern), recursive=True)
                )
            
            logger.info(f"Found {len(self.parquet_files)} parquet files")
            
        except Exception as e:
            logger.error(f"Error initializing cold_metadata: {e}")
            raise

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

    def transfer_all_schemas(self):
        """Transfer schema information for all files in cold_metadata to red-hot memory."""
        # Print FAISS storage location
        print(f"\nFAISS storage location: {self.red_hot.storage_path}")
        print(f"Data directory: {self.data_dir}")
        
        files = self.get_parquet_files()
        total_files = len(files)
        logger.info(f"Found {total_files} files in cold_metadata")
        
        stats = {
            'total_files': total_files,
            'processed_files': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'by_source_type': {
                'base': 0,
                'divisions': 0,
                'transportation': 0,
                'unknown': 0
            }
        }
        
        for file_path in files:
            try:
                self.transfer_schema_to_redhot(file_path)
                stats['processed_files'] += 1
                stats['successful_transfers'] += 1
                
                # Update source type stats
                source_type = 'unknown'
                if 'base' in file_path:
                    source_type = 'base'
                elif 'divisions' in file_path:
                    source_type = 'divisions'
                elif 'transportation' in file_path:
                    source_type = 'transportation'
                stats['by_source_type'][source_type] += 1
                
                # Log progress periodically
                if stats['processed_files'] % 100 == 0:
                    self._log_progress(stats)
                    
            except Exception as e:
                logger.error(f"Error transferring schema for {file_path}: {e}")
                stats['failed_transfers'] += 1
                stats['processed_files'] += 1
        
        # Log final statistics
        self._log_final_stats(stats)
        
        # Print final FAISS index size
        print(f"\nFinal FAISS index size: {self.red_hot.index.ntotal} vectors")
        print(f"FAISS index dimension: {self.red_hot.dimension}")
        
        return stats

    def _log_progress(self, stats):
        """Log progress of the transfer process."""
        progress = (stats['processed_files'] / stats['total_files']) * 100
        logger.info(f"Progress: {progress:.2f}% ({stats['processed_files']}/{stats['total_files']} files)")
        logger.info(f"Successful: {stats['successful_transfers']}, Failed: {stats['failed_transfers']}")

    def _log_final_stats(self, stats):
        """Log final statistics of the transfer process."""
        logger.info("\n=== Transfer Complete ===")
        logger.info(f"Total files processed: {stats['processed_files']}/{stats['total_files']}")
        logger.info(f"Successful transfers: {stats['successful_transfers']}")
        logger.info(f"Failed transfers: {stats['failed_transfers']}")
        logger.info("\nBy source type:")
        for source_type, count in stats['by_source_type'].items():
            logger.info(f"  {source_type}: {count} files")

def main():
    """Main function to run the transfer process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add project root to Python path
    project_root = str(Path(__file__).parent.parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added {project_root} to Python path")
    
    transfer = ColdToRedHot()
    stats = transfer.transfer_all_schemas()
    
    # Print final summary
    print("\nTransfer Summary:")
    print(f"Total files: {stats['total_files']}")
    print(f"Successfully transferred: {stats['successful_transfers']}")
    print(f"Failed transfers: {stats['failed_transfers']}")
    print("\nBy source type:")
    for source_type, count in stats['by_source_type'].items():
        if count > 0:  # Only show non-zero counts
            print(f"  {source_type}: {count} files")

if __name__ == "__main__":
    import sys
    main() 
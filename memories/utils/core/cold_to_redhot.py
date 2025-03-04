import logging
from pathlib import Path
import pandas as pd
import duckdb
import os
from typing import Dict, List, Tuple, Optional
from memories.core.red_hot import RedHotMemory
from memories.core.cold import ColdMemory
import pyarrow.parquet as pq
import glob
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class ColdToRedHot:
    def __init__(self):
        """Initialize cold to red-hot transfer."""
        # Get project root directory
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Set up data directories
        self.data_dir = os.path.join(project_root, "data")
        self.faiss_dir = os.path.join(self.data_dir, "red_hot")
        
        # Initialize components
        self.cold = ColdMemory()
        self.red_hot = RedHotMemory()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Debug prints
        print("\nDebug info:")
        print(f"Project root: {project_root}")
        print(f"Data directory: {self.data_dir}")
        print(f"FAISS storage location: {self.faiss_dir}")
        print(f"RedHotMemory methods: {dir(self.red_hot)}")
        print(f"Has add_vector: {'add_vector' in dir(self.red_hot)}\n")
        
        logger.info(f"Initialized ColdToRedHot")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"FAISS storage location: {self.faiss_dir}")

    def get_schema_info(self, file_path: str):
        """Get schema information from a parquet file."""
        try:
            # Read parquet file schema using pandas directly
            df = pd.read_parquet(file_path)
            
            # Get schema information
            schema_info = {
                'file_path': file_path,
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'type': 'schema'
            }
            
            # Create text representation for embedding
            column_text = " ".join(schema_info['columns'])
            
            return schema_info, column_text
            
        except Exception as e:
            logger.error(f"Error reading schema from {file_path}: {e}")
            raise

    def transfer_schema_to_redhot(self, file_path: str):
        """Transfer schema information from a parquet file to red-hot memory."""
        try:
            # Get schema information and text for embedding
            schema_info, column_text = self.get_schema_info(file_path)
            
            # Create embedding from column names
            embedding = self.model.encode([column_text])[0]
            
            # Add to red-hot memory
            self.red_hot.add_vector(embedding, metadata=schema_info)
            
            logger.debug(f"Transferred schema for {file_path}")
            
        except Exception as e:
            logger.error(f"Error transferring schema for {file_path}: {e}")
            raise

    def transfer_all_schemas(self):
        """Transfer schema information from cold storage metadata to red-hot memory."""
        # Get all schemas from cold storage
        schemas = self.cold.get_all_schemas()
        total_schemas = len(schemas)
        
        logger.info(f"Found {total_schemas} schemas in cold storage")
        
        stats = {
            'total_files': total_schemas,
            'processed_files': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'by_source_type': {
                'base': 0,
                'divisions': 0,
                'transportation': 0,
                'buildings': 0,
                'unknown': 0
            }
        }
        
        for schema in schemas:
            try:
                # Create text from column names
                columns = schema.get('columns', [])
                column_text = " ".join(columns)
                
                # Create embedding
                embedding = self.model.encode([column_text])[0]
                
                # Add to red-hot memory
                self.red_hot.add_vector(
                    embedding,
                    metadata={
                        'file_path': schema.get('file_path', ''),
                        'columns': columns,
                        'dtypes': schema.get('dtypes', {}),
                        'type': 'schema'
                    }
                )
                
                stats['processed_files'] += 1
                stats['successful_transfers'] += 1
                
                # Update source type stats
                source_type = 'unknown'
                file_path = schema.get('file_path', '')
                if 'base' in file_path:
                    source_type = 'base'
                elif 'divisions' in file_path:
                    source_type = 'divisions'
                elif 'transportation' in file_path:
                    source_type = 'transportation'
                elif 'buildings' in file_path:
                    source_type = 'buildings'
                stats['by_source_type'][source_type] += 1
                
                # Log progress periodically
                if stats['processed_files'] % 100 == 0:
                    self._log_progress(stats)
                    
            except Exception as e:
                logger.error(f"Error transferring schema: {e}")
                stats['failed_transfers'] += 1
                stats['processed_files'] += 1
        
        # Log final statistics
        self._log_final_stats(stats)
        
        # Print final FAISS index size and location
        print(f"\nFinal FAISS index size: {self.red_hot.index.ntotal} vectors")
        print(f"FAISS index dimension: {self.red_hot.dimension}")
        print(f"FAISS storage location: {self.faiss_dir}")
        
        return stats

    def _log_progress(self, stats):
        """Log progress of the transfer process."""
        progress = (stats['processed_files'] / stats['total_files']) * 100 if stats['total_files'] > 0 else 0
        logger.info(f"Progress: {progress:.2f}% ({stats['processed_files']}/{stats['total_files']} schemas)")
        logger.info(f"Successful: {stats['successful_transfers']}, Failed: {stats['failed_transfers']}")

    def _log_final_stats(self, stats):
        """Log final statistics of the transfer process."""
        logger.info("\n=== Transfer Complete ===")
        logger.info(f"Total schemas processed: {stats['processed_files']}/{stats['total_files']}")
        logger.info(f"Successful transfers: {stats['successful_transfers']}")
        logger.info(f"Failed transfers: {stats['failed_transfers']}")
        logger.info("\nBy source type:")
        for source_type, count in stats['by_source_type'].items():
            if count > 0:  # Only show non-zero counts
                logger.info(f"  {source_type}: {count} schemas")

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
    print(f"Total schemas: {stats['total_files']}")
    print(f"Successfully transferred: {stats['successful_transfers']}")
    print(f"Failed transfers: {stats['failed_transfers']}")
    print("\nBy source type:")
    for source_type, count in stats['by_source_type'].items():
        if count > 0:  # Only show non-zero counts
            print(f"  {source_type}: {count} schemas")

if __name__ == "__main__":
    import sys
    main() 
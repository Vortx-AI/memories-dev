#!/usr/bin/env python3

import os
from pathlib import Path
import duckdb
from memories.core.memory_manager import MemoryManager
from memories.utils.text.embeddings import get_encoder

def initialize_database(db_path: Path):
    """Initialize the database schema."""
    print("Initializing database schema...")
    
    # Create database directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = duckdb.connect(str(db_path))
    
    try:
        # Enable external access for parquet files
        conn.execute("SET enable_external_access=true")
        
        # Create file_metadata table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_metadata (
                file_path VARCHAR PRIMARY KEY,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("Database schema initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()

def main():
    # Source directory containing parquet files
    source_dir = Path("/Users/jaya/geo_memories")
    if not source_dir.exists():
        raise ValueError(f"Source directory not found: {source_dir}")

    print(f"\n=== Importing Geo Memories from {source_dir} ===\n")
    
    # Initialize database
    db_path = Path("cold/cold.db")
    initialize_database(db_path)
    
    # Initialize vector encoder
    print("Initializing vector encoder...")
    vector_encoder = get_encoder()
    
    # Initialize memory manager with cold storage enabled
    print("Initializing memory manager...")
    memory_manager = MemoryManager(
        vector_encoder=vector_encoder,
        enable_hot=False,     # Disable Redis dependency
        enable_cold=True,     # Enable cold storage for parquet files
        enable_warm=False,    # Disable warm storage
        enable_glacier=False  # Disable glacier storage
    )
    
    # Configure cold storage with 10GB max size
    print("Configuring cold storage...")
    memory_manager.configure_tiers(
        cold_config={
            'path': 'cold',
            'max_size': 10737418240,  # 10GB
            'duckdb_config': {
                'memory_limit': '8GB',
                'threads': 4,
                'enable_external_access': True
            }
        }
    )
    
    print("\nStarting parquet file import...")
    try:
        # Import parquet files
        results = memory_manager.batch_import_parquet(
            folder_path=source_dir,
            theme="geo",
            tag="location",
            recursive=True,
            pattern="*.parquet"
        )
        
        # Print detailed results
        print("\nImport Results:")
        print(f"Files processed: {results['files_processed']}")
        print(f"Records imported: {results['records_imported']}")
        print(f"Total size: {results['total_size'] / (1024*1024):.2f} MB")
        
        if results['errors']:
            print("\nErrors encountered:")
            for error in results['errors']:
                print(f"- {error}")
        
        print("\nImport completed successfully!")
        
    except Exception as e:
        print(f"\nError during import: {str(e)}")
        raise
    
    finally:
        print("\nCleaning up...")
        memory_manager.cleanup()

if __name__ == "__main__":
    main() 
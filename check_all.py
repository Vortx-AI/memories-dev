#!/usr/bin/env python3

import asyncio
import logging
from memories.core.memory_catalog import memory_catalog
from memories.core.warm import WarmMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_all():
    """Check both memory catalog and persistent database."""
    try:
        print("\nChecking Memory Catalog:")
        print("=" * 80)
        
        # Query the catalog for all warm tier data
        results = await memory_catalog.get_tier_data("warm")
        
        if not results:
            print("No entries found in memory catalog for warm tier")
        else:
            print(f"\nFound {len(results)} entries in memory catalog (warm tier):")
            for entry in results:
                print(f"\nData ID: {entry['data_id']}")
                print("-" * 80)
                print(f"Location (table): {entry['location']}")
                print(f"Table name: {entry['table_name']}")
                print(f"Tags: {entry['tags']}")
                print(f"Additional metadata: {entry['additional_meta']}")
        
        print("\nChecking Persistent Database:")
        print("=" * 80)
        
        # Initialize warm memory and connect to persistent database
        warm = WarmMemory()
        try:
            # Connect to the persistent database
            db_name = "dubai_persistent"
            con = warm.get_connection(db_name)
            
            # Print database location
            logger.info(f"Connected to database: {db_name}")
            db_path = con.execute("PRAGMA database_list").fetchall()
            for db in db_path:
                logger.info(f"Database location: {db[2] if db[2] else 'in-memory'}")
            
            # Get list of tables
            tables = con.execute("SHOW TABLES").fetchall()
            
            if not tables:
                print("No tables found in the persistent database.")
                return
                
            print(f"\nFound {len(tables)} tables in the persistent database:")
            
            # For each table, show basic info
            for table in tables:
                table_name = table[0]
                try:
                    # Get row count
                    row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    
                    # Get column information
                    columns = con.execute(f"DESCRIBE {table_name}").fetchall()
                    column_names = [col[0] for col in columns]
                    
                    print(f"\nTable: {table_name}")
                    print("-" * 60)
                    print(f"Row count: {row_count}")
                    print(f"Columns: {', '.join(column_names)}")
                    
                except Exception as e:
                    print(f"Error reading table {table_name}: {e}")
        
        finally:
            # Clean up warm memory
            warm.cleanup()

    except Exception as e:
        logger.error(f"Error during checks: {e}")

if __name__ == "__main__":
    asyncio.run(check_all()) 
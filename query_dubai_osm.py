#!/usr/bin/env python
"""
Script to query Dubai OSM data that has been imported to warm memory.
This demonstrates how to access and use the imported data.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any, List

from memories.core.memory_store import MemoryStore
from memories.core.warm import WarmMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("query_dubai_osm.log")
    ]
)
logger = logging.getLogger(__name__)

# Default database name in warm memory
DEFAULT_DB_NAME = "dubai_osm"

async def list_tables(db_name: str = DEFAULT_DB_NAME) -> List[str]:
    """
    List all tables in the warm memory database.
    
    Args:
        db_name: Name of the database in warm memory
        
    Returns:
        List of table names
    """
    try:
        # Initialize warm memory
        warm_memory = WarmMemory()
        
        # Get connection to the database
        con = warm_memory.get_connection(db_name)
        
        # Get list of tables
        result = con.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT IN ('warm_data', 'warm_tags')
        """).fetchall()
        
        # Extract table names
        table_names = [row[0] for row in result]
        
        return table_names
    
    except Exception as e:
        logger.error(f"Error listing tables: {e}", exc_info=True)
        return []
    finally:
        # Clean up resources
        warm_memory.cleanup()

async def get_table_info(table_name: str, db_name: str = DEFAULT_DB_NAME) -> Dict[str, Any]:
    """
    Get information about a table in warm memory.
    
    Args:
        table_name: Name of the table
        db_name: Name of the database in warm memory
        
    Returns:
        Dictionary with table information
    """
    try:
        # Initialize warm memory
        warm_memory = WarmMemory()
        
        # Get connection to the database
        con = warm_memory.get_connection(db_name)
        
        # Get table schema
        schema_result = con.execute(f"DESCRIBE {table_name}").fetchall()
        
        # Get row count
        count_result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        
        # Get sample data (first 5 rows)
        sample_result = con.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
        column_names = [desc[0] for desc in con.description]
        
        # Format sample data as list of dictionaries
        sample_data = []
        for row in sample_result:
            sample_data.append(dict(zip(column_names, row)))
        
        return {
            "table_name": table_name,
            "schema": [{"column": row[0], "type": row[1]} for row in schema_result],
            "row_count": count_result[0] if count_result else 0,
            "sample_data": sample_data
        }
    
    except Exception as e:
        logger.error(f"Error getting table info for {table_name}: {e}", exc_info=True)
        return {}
    finally:
        # Clean up resources
        warm_memory.cleanup()

async def execute_query(query: str, db_name: str = DEFAULT_DB_NAME) -> List[Dict[str, Any]]:
    """
    Execute a SQL query on the warm memory database.
    
    Args:
        query: SQL query to execute
        db_name: Name of the database in warm memory
        
    Returns:
        Query results as a list of dictionaries
    """
    try:
        # Initialize warm memory
        warm_memory = WarmMemory()
        
        # Get connection to the database
        con = warm_memory.get_connection(db_name)
        
        # Execute query
        result = con.execute(query).fetchall()
        
        # Get column names
        column_names = [desc[0] for desc in con.description]
        
        # Format results as list of dictionaries
        formatted_results = []
        for row in result:
            formatted_results.append(dict(zip(column_names, row)))
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        return []
    finally:
        # Clean up resources
        warm_memory.cleanup()

async def main():
    """Main function to demonstrate querying Dubai OSM data."""
    try:
        # List all tables
        tables = await list_tables()
        
        if not tables:
            logger.error("No tables found in the database. Make sure to import the data first.")
            return
        
        print(f"Found {len(tables)} tables in the database:")
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table}")
        
        # Get info for the first table
        if tables:
            first_table = tables[0]
            print(f"\nInformation for table '{first_table}':")
            table_info = await get_table_info(first_table)
            
            print(f"Schema:")
            for column in table_info.get("schema", []):
                print(f"  - {column['column']} ({column['type']})")
            
            print(f"Row count: {table_info.get('row_count', 0)}")
            
            print(f"Sample data (first 5 rows):")
            for row in table_info.get("sample_data", []):
                print(f"  {row}")
        
        # Example: Execute a custom query
        print("\nExecuting a custom query...")
        
        # This is just an example query - adjust based on the actual tables and columns in your data
        example_query = f"SELECT * FROM {tables[0]} LIMIT 10"
        
        results = await execute_query(example_query)
        
        print(f"Query results (first 10 rows from {tables[0]}):")
        for row in results:
            print(f"  {row}")
    
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 
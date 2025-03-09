#!/usr/bin/env python3

import asyncio
from memories.core.warm import WarmMemory

async def check_tables():
    """List all tables in the database and show their row counts."""
    # Initialize warm memory
    warm = WarmMemory()
    
    # Get the default connection
    con = warm.default_con
    
    # Get list of tables
    tables = con.execute("SHOW TABLES").fetchall()
    
    if not tables:
        print("No tables found in the database.")
        return
        
    print(f"Found {len(tables)} tables in the database:")
    print("-" * 60)
    print(f"{'Table Name':<30} {'Row Count':<15}")
    print("-" * 60)
    
    # Get row count for each table
    for table in tables:
        table_name = table[0]
        try:
            row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"{table_name:<30} {row_count:<15}")
        except Exception as e:
            print(f"{table_name:<30} Error: {str(e)}")
    
    # Clean up
    warm.cleanup()

if __name__ == "__main__":
    asyncio.run(check_tables()) 
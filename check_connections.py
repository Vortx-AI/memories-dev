#!/usr/bin/env python3

import asyncio
import os
from memories.core.warm import WarmMemory

async def check_all_connections():
    """Check all connections in WarmMemory and list tables in each."""
    # Initialize warm memory
    warm = WarmMemory()
    
    # Print information about the default connection
    print(f"Default connection path: {warm.storage_path}")
    print(f"Connections dictionary: {warm.connections.keys()}")
    
    # Check the default connection
    print("\nTables in default connection:")
    print("-" * 60)
    tables = warm.default_con.execute("SHOW TABLES").fetchall()
    if not tables:
        print("No tables found in default connection")
    else:
        print(f"{'Table Name':<30} {'Row Count':<15}")
        print("-" * 60)
        for table in tables:
            table_name = table[0]
            try:
                row_count = warm.default_con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                print(f"{table_name:<30} {row_count:<15}")
            except Exception as e:
                print(f"{table_name:<30} Error: {str(e)}")
    
    # Check if there are any other database files in the storage path
    if warm.storage_path:
        print("\nChecking for database files in storage path:")
        db_files = [f for f in os.listdir(warm.storage_path) if f.endswith('.duckdb')]
        print(f"Found {len(db_files)} database files: {', '.join(db_files)}")
        
        # Try to connect to each database file and list tables
        for db_file in db_files:
            db_name = db_file.replace('.duckdb', '')
            print(f"\nTrying to access database: {db_name}")
            try:
                con = warm.get_connection(db_name)
                tables = con.execute("SHOW TABLES").fetchall()
                if not tables:
                    print(f"No tables found in {db_name}")
                else:
                    print(f"Found {len(tables)} tables in {db_name}:")
                    print(f"{'Table Name':<30} {'Row Count':<15}")
                    print("-" * 60)
                    for table in tables:
                        table_name = table[0]
                        try:
                            row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                            print(f"{table_name:<30} {row_count:<15}")
                        except Exception as e:
                            print(f"{table_name:<30} Error: {str(e)}")
            except Exception as e:
                print(f"Error accessing {db_name}: {e}")
    
    # Clean up
    warm.cleanup()

if __name__ == "__main__":
    asyncio.run(check_all_connections()) 
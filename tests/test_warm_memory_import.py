"""Tests for warm memory import functionality."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
import json
from pathlib import Path
import os
import tempfile
import duckdb

from memories.core.warm import WarmMemory
from memories.core.memory_manager import MemoryManager
from memories.core.memory_store import memory_store

# Mock the MemoryManager for testing
@pytest.fixture
def mock_memory_manager():
    """Mock memory manager with configuration."""
    with patch('memories.core.memory_manager.MemoryManager', autospec=True) as mock:
        instance = mock.return_value
        instance.config = {
            'memory': {
                'base_path': './data/memory',
                'warm': {
                    'path': 'warm',
                    'duckdb': {
                        'memory_limit': '1GB',
                        'threads': 2
                    }
                }
            }
        }
        # Create a mock DuckDB connection
        instance.con = duckdb.connect(database=':memory:')
        return instance

@pytest.fixture
def warm_memory(mock_memory_manager):
    """Create a WarmMemory instance with mocked dependencies."""
    with patch('memories.core.warm.MemoryManager', return_value=mock_memory_manager):
        memory = WarmMemory()
        yield memory
        # Clean up after tests
        memory.cleanup()

@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample DataFrame
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Item 1', 'Item 2', 'Item 3'],
            'value': [10.5, 20.5, 30.5]
        })
        
        # Save as CSV
        csv_path = os.path.join(temp_dir, 'sample_data.csv')
        df.to_csv(csv_path, index=False)
        
        yield csv_path

@pytest.fixture
def sample_duckdb_file():
    """Create a sample DuckDB file with tables for testing."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample DuckDB file
        db_path = os.path.join(temp_dir, 'sample.duckdb')
        
        # Connect to the database
        con = duckdb.connect(database=db_path)
        
        # Create and populate tables
        con.execute("""
            CREATE TABLE users (
                id INTEGER,
                name VARCHAR,
                email VARCHAR
            )
        """)
        
        con.execute("""
            INSERT INTO users VALUES
            (1, 'User 1', 'user1@example.com'),
            (2, 'User 2', 'user2@example.com'),
            (3, 'User 3', 'user3@example.com')
        """)
        
        con.execute("""
            CREATE TABLE products (
                id INTEGER,
                name VARCHAR,
                price DOUBLE
            )
        """)
        
        con.execute("""
            INSERT INTO products VALUES
            (101, 'Product 1', 99.99),
            (102, 'Product 2', 149.99),
            (103, 'Product 3', 199.99)
        """)
        
        # Close the connection
        con.close()
        
        yield db_path

@pytest.mark.asyncio
async def test_import_from_csv(warm_memory, sample_csv_file):
    """Test importing data from a CSV file."""
    # Import the CSV file
    result = await warm_memory.import_from_csv(
        csv_file=sample_csv_file,
        metadata={"source": "test"},
        tags=["csv", "test"]
    )
    
    # Check the result
    assert result["success"] is True
    assert "data_id" in result
    assert "table_name" in result
    
    # Verify the table was created
    table_exists = warm_memory.default_con.execute(f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='{result["table_name"]}'
    """).fetchone()
    
    assert table_exists is not None
    
    # Verify data was imported correctly
    data = warm_memory.default_con.execute(f"SELECT * FROM {result['table_name']}").fetchall()
    assert len(data) == 3
    
    # Verify metadata was stored in warm_data
    warm_data = warm_memory.default_con.execute("""
        SELECT * FROM warm_data WHERE id = ?
    """, [result["data_id"]]).fetchone()
    
    assert warm_data is not None
    
    # Verify tags were stored
    tags = warm_memory.default_con.execute("""
        SELECT * FROM warm_tags WHERE data_id = ?
    """, [result["data_id"]]).fetchall()
    
    assert len(tags) == 2  # "csv" and "test"

@pytest.mark.asyncio
async def test_import_from_duckdb(warm_memory, sample_duckdb_file):
    """Test importing tables from another DuckDB database."""
    # Import all tables from the DuckDB file
    result = await warm_memory.import_from_duckdb(
        source_db_file=sample_duckdb_file,
        metadata={"source": "test"},
        tags=["duckdb", "test"]
    )
    
    # Check the result
    assert result["success"] is True
    assert "imported_tables" in result
    assert "data_ids" in result
    assert len(result["imported_tables"]) == 2  # users and products
    
    # Verify the tables were created
    for table_name in ["users", "products"]:
        table_exists = warm_memory.default_con.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{table_name}'
        """).fetchone()
        
        assert table_exists is not None
        
        # Verify data was imported correctly
        data = warm_memory.default_con.execute(f"SELECT * FROM {table_name}").fetchall()
        assert len(data) == 3
        
        # Verify metadata was stored in warm_data
        data_id = result["data_ids"][table_name]
        warm_data = warm_memory.default_con.execute("""
            SELECT * FROM warm_data WHERE id = ?
        """, [data_id]).fetchone()
        
        assert warm_data is not None
        
        # Verify tags were stored
        tags = warm_memory.default_con.execute("""
            SELECT * FROM warm_tags WHERE data_id = ?
        """, [data_id]).fetchall()
        
        assert len(tags) == 2  # "duckdb" and "test"

@pytest.mark.asyncio
async def test_import_specific_tables_from_duckdb(warm_memory, sample_duckdb_file):
    """Test importing specific tables from another DuckDB database."""
    # Import only the users table
    result = await warm_memory.import_from_duckdb(
        source_db_file=sample_duckdb_file,
        tables=["users"],
        metadata={"source": "test"},
        tags=["duckdb", "test"]
    )
    
    # Check the result
    assert result["success"] is True
    assert "imported_tables" in result
    assert "data_ids" in result
    assert len(result["imported_tables"]) == 1  # only users
    assert "users" in result["imported_tables"]
    assert "products" not in result["imported_tables"]
    
    # Verify the users table was created
    users_exists = warm_memory.default_con.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='users'
    """).fetchone()
    
    assert users_exists is not None
    
    # Verify the products table was not created
    products_exists = warm_memory.default_con.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='products'
    """).fetchone()
    
    assert products_exists is None 
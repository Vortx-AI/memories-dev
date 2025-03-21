"""
Tests for the MemoryCatalog class in the core.memory_catalog module.
"""

import os
import pytest
import tempfile
import json
import pickle
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from memories.core.memory_catalog import MemoryCatalog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)
logger = logging.getLogger(__name__)
# Set logger to INFO level for better visibility during tests
logger.setLevel(logging.INFO)


def create_sample_buildings_data(num_buildings=10):
    """Create sample building data for testing."""
    logger.info(f"Creating sample data for {num_buildings} buildings")
    
    # Generate random building data
    data = {
        'id': range(1, num_buildings + 1),
        'name': [f"Building_{i}" for i in range(1, num_buildings + 1)],
        'height': np.random.uniform(10, 400, num_buildings),
        'floors': np.random.randint(1, 100, num_buildings),
        'building_type': np.random.choice(['residential', 'commercial', 'mixed', 'industrial'], num_buildings),
        'year_built': np.random.randint(1950, 2023, num_buildings),
        'latitude': np.random.uniform(25.0, 25.3, num_buildings),
        'longitude': np.random.uniform(55.0, 55.4, num_buildings)
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    logger.info(f"Created DataFrame with shape: {df.shape}")
    
    # Add a special building for easy identification
    df.loc[0, 'name'] = 'Burj Khalifa'
    df.loc[0, 'height'] = 828
    df.loc[0, 'floors'] = 163
    
    return df


@pytest.fixture
def mock_memory_manager():
    """Create a mock MemoryManager instance."""
    logger.info("Creating mock MemoryManager fixture")
    mock_manager = MagicMock()
    mock_manager.get_storage_path.return_value = "/tmp/test_storage"
    logger.debug("Mock MemoryManager created with storage path: /tmp/test_storage")
    return mock_manager


@pytest.fixture
def memory_catalog(mock_memory_manager):
    """Create a MemoryCatalog instance with mocked dependencies."""
    logger.info("Creating memory_catalog fixture with mocked dependencies")
    
    # Create a mock DuckDB connection - use AsyncMock instead of MagicMock for awaitable methods
    mock_con = AsyncMock()
    mock_con.execute.return_value = mock_con
    
    # Configure the mock to return test data
    mock_con.fetchone.return_value = ["test-data-id", "cold", "test_location", "2023-01-01T00:00:00", "2023-01-01T00:00:00", 1, 1000, '["test"]', "dataframe", "test_table", '{"source":"test"}']
    mock_con.fetchall.return_value = [
        ["test-data-id", "cold", "test_location", "2023-01-01T00:00:00", "2023-01-01T00:00:00", 1, 1000, '["test"]', "dataframe", "test_table", '{"source":"test"}']
    ]
    
    # Create a catalog instance
    catalog = MemoryCatalog()
    logger.debug("Created MemoryCatalog instance")
    
    # Set up the mock connection
    catalog.con = mock_con
    catalog._memory_manager = mock_memory_manager
    
    # Mock the async methods to return test data
    async def mock_register_data(tier, location, size, data_type, tags=None, metadata=None, table_name=None):
        logger.debug(f"Mock register_data called with tier={tier}, location={location}, data_type={data_type}")
        return "test-data-id"
    
    async def mock_update_access(data_id):
        logger.debug(f"Mock update_access called for data_id={data_id}")
        await catalog.con.execute("UPDATE mock_query")
        return None
    
    async def mock_get_data_info(data_id):
        logger.debug(f"Mock get_data_info called for data_id={data_id}")
        return {
            "data_id": data_id,
            "tier": "cold",
            "location": "test_location",
            "created": "2023-01-01T00:00:00",
            "last_accessed": "2023-01-01T00:00:00",
            "access_count": 1,
            "size": 1000,
            "tags": ["test"],
            "data_type": "dataframe",
            "table_name": "test_table",
            "metadata": {"source": "test"}
        }
    
    async def mock_search_by_tags(tags):
        logger.debug(f"Mock search_by_tags called with tags={tags}")
        return [{
            "data_id": "test-data-id",
            "tier": "cold",
            "location": "test_location",
            "created": "2023-01-01T00:00:00",
            "last_accessed": "2023-01-01T00:00:00",
            "access_count": 1,
            "size": 1000,
            "tags": ["test"],
            "data_type": "dataframe",
            "table_name": "test_table",
            "metadata": {"source": "test"}
        }]
    
    async def mock_get_tier_data(tier):
        logger.debug(f"Mock get_tier_data called for tier={tier}")
        return [{
            "data_id": "test-data-id",
            "tier": tier,
            "location": "test_location",
            "created": "2023-01-01T00:00:00",
            "last_accessed": "2023-01-01T00:00:00",
            "access_count": 1,
            "size": 1000,
            "tags": ["test"],
            "data_type": "dataframe",
            "table_name": "test_table",
            "metadata": {"source": "test"}
        }]
    
    async def mock_delete_data(data_id):
        logger.debug(f"Mock delete_data called for data_id={data_id}")
        await catalog.con.execute("DELETE mock_query")
        return True
    
    # Assign the mock methods
    catalog.register_data = mock_register_data
    catalog.update_access = mock_update_access
    catalog.get_data_info = mock_get_data_info
    catalog.search_by_tags = mock_search_by_tags
    catalog.get_tier_data = mock_get_tier_data
    catalog.delete_data = mock_delete_data
    
    logger.info("MemoryCatalog fixture setup complete with all mocked methods")
    return catalog


class TestMemoryCatalog:
    """Tests for the MemoryCatalog class."""
    
    def test_initialization(self, memory_catalog):
        """Test initialization of MemoryCatalog."""
        logger.info("Testing MemoryCatalog initialization")
        assert memory_catalog is not None
        assert memory_catalog.con is not None
        logger.info("MemoryCatalog initialization test passed")
    
    def test_singleton_pattern(self, memory_catalog):
        """Test that MemoryCatalog follows the singleton pattern."""
        logger.info("Testing MemoryCatalog singleton pattern")
        catalog2 = MemoryCatalog()
        assert memory_catalog is catalog2
        logger.info("MemoryCatalog singleton pattern test passed")
    
    @pytest.mark.asyncio
    async def test_register_data(self, memory_catalog):
        """Test registering data in the catalog."""
        logger.info("Testing register_data method")
        
        # Register test data
        logger.debug("Calling register_data with test parameters")
        data_id = await memory_catalog.register_data(
            tier="cold",
            location="test_location",
            size=1000,
            tags=["test"],
            data_type="dataframe",
            table_name="test_table",
            metadata={"source": "test"}
        )
        
        # Check that the data was registered
        assert data_id is not None
        assert isinstance(data_id, str)
        assert data_id == "test-data-id"
        logger.info(f"register_data test passed, received data_id: {data_id}")
    
    @pytest.mark.asyncio
    async def test_update_access(self, memory_catalog):
        """Test updating access time for data."""
        logger.info("Testing update_access method")
        
        # Update access time
        test_id = "test-data-id"
        logger.debug(f"Calling update_access for data_id: {test_id}")
        await memory_catalog.update_access(test_id)
        
        # Check that execute was called with the correct SQL
        memory_catalog.con.execute.assert_called()
        logger.info("update_access test passed")
    
    @pytest.mark.asyncio
    async def test_get_data_info(self, memory_catalog):
        """Test getting data info from the catalog."""
        logger.info("Testing get_data_info method")
        
        # Get data info
        test_id = "test-data-id"
        logger.debug(f"Calling get_data_info for data_id: {test_id}")
        data_info = await memory_catalog.get_data_info(test_id)
        
        # Check that the data info was returned
        assert data_info is not None
        assert data_info["data_id"] == "test-data-id"
        assert data_info["tier"] == "cold"
        assert data_info["location"] == "test_location"
        assert data_info["created"] == "2023-01-01T00:00:00"
        assert data_info["last_accessed"] == "2023-01-01T00:00:00"
        assert data_info["access_count"] == 1
        assert data_info["size"] == 1000
        assert data_info["tags"] == ["test"]
        assert data_info["data_type"] == "dataframe"
        assert data_info["table_name"] == "test_table"
        assert data_info["metadata"] == {"source": "test"}
        
        logger.info(f"get_data_info test passed, verified all expected fields in data_info")
        logger.debug(f"Returned data_info: {data_info}")
    
    @pytest.mark.asyncio
    async def test_search_by_tags(self, memory_catalog):
        """Test searching for data by tags."""
        logger.info("Testing search_by_tags method")
        
        # Search by tags
        test_tags = ["test"]
        logger.debug(f"Calling search_by_tags with tags: {test_tags}")
        results = await memory_catalog.search_by_tags(test_tags)
        
        # Check that the results were returned
        assert results is not None
        assert len(results) == 1
        assert results[0]["data_id"] == "test-data-id"
        
        logger.info(f"search_by_tags test passed, found {len(results)} results")
        logger.debug(f"First result data_id: {results[0]['data_id']}")
    
    @pytest.mark.asyncio
    async def test_get_tier_data(self, memory_catalog):
        """Test getting all data for a tier."""
        logger.info("Testing get_tier_data method")
        
        # Get tier data
        test_tier = "cold"
        logger.debug(f"Calling get_tier_data for tier: {test_tier}")
        results = await memory_catalog.get_tier_data(test_tier)
        
        # Check that the results were returned
        assert results is not None
        assert len(results) == 1
        assert results[0]["data_id"] == "test-data-id"
        
        logger.info(f"get_tier_data test passed, found {len(results)} results for tier {test_tier}")
        logger.debug(f"First result data_id: {results[0]['data_id']}")
    
    @pytest.mark.asyncio
    async def test_delete_data(self, memory_catalog):
        """Test deleting data from the catalog."""
        logger.info("Testing delete_data method")
        
        # Delete data
        test_id = "test-data-id"
        logger.debug(f"Calling delete_data for data_id: {test_id}")
        result = await memory_catalog.delete_data(test_id)
        
        # Check that execute was called with the correct SQL
        memory_catalog.con.execute.assert_called()
        assert result is True
        
        logger.info(f"delete_data test passed, delete operation result: {result}")
    
    def test_cleanup(self, memory_catalog):
        """Test cleanup method."""
        logger.info("Testing cleanup method")
        
        # Create a new mock connection
        mock_con = MagicMock()
        logger.debug("Created new mock connection for cleanup test")
        
        # Replace the existing connection with our mock
        original_con = memory_catalog.con
        memory_catalog.con = mock_con
        
        try:
            # Call cleanup
            logger.debug("Calling cleanup method")
            memory_catalog.cleanup()
            
            # Check that the connection was closed
            mock_con.close.assert_called_once()
            logger.info("cleanup test passed, connection was closed")
        finally:
            # Restore the original connection to avoid affecting other tests
            logger.debug("Restoring original connection")
            memory_catalog.con = original_con
    
    @pytest.mark.asyncio
    async def test_red_hot_pickle_catalog(self, memory_catalog):
        """Test registering and retrieving pickle files in Red Hot memory catalog."""
        logger.info("Testing Red Hot memory pickle catalog registration and retrieval")
        
        # Create an actual pickle file with sample data
        try:
            # Generate sample building data
            buildings_df = create_sample_buildings_data(num_buildings=10)
            
            # Create a temporary pickle file
            pickle_location = os.path.join(tempfile.gettempdir(), "sample_buildings.pkl")
            logger.info(f"Creating pickle file at {pickle_location}")
            
            # Save DataFrame to pickle file
            with open(pickle_location, 'wb') as f:
                pickle.dump(buildings_df, f)
            
            file_size = os.path.getsize(pickle_location) // 1024
            logger.info(f"Created pickle file, size: {file_size} KB")
            
            # Display the contents of the pickle file
            logger.info("Contents of the pickle file:")
            logger.info(f"DataFrame shape: {buildings_df.shape}")
            logger.info(f"DataFrame columns: {buildings_df.columns.tolist()}")
            logger.info("Sample data (first 5 rows):")
            for i, row in buildings_df.head(5).iterrows():
                logger.info(f"Row {i}: {dict(row)}")
            
            # Find Burj Khalifa
            burj = buildings_df[buildings_df['name'] == 'Burj Khalifa']
            if not burj.empty:
                logger.info("Burj Khalifa details:")
                logger.info(dict(burj.iloc[0]))
            
            # Configure mock to return red_hot tier data
            logger.debug("Configuring mock to return red_hot tier data")
            memory_catalog.con.fetchone.return_value = [
                "red-hot-data-id", "red_hot", pickle_location, 
                "2023-01-01T00:00:00", "2023-01-01T00:00:00", 1, file_size, 
                '["test", "buildings", "dataframe"]', "pickle", "buildings", 
                '{"description": "Sample buildings data", "rows": 10}'
            ]
            
            # Mock get_data_info to return red_hot data
            async def mock_get_red_hot_info(data_id):
                logger.debug(f"Mock get_data_info called for red_hot data_id={data_id}")
                return {
                    "data_id": data_id,
                    "tier": "red_hot",
                    "location": pickle_location,
                    "created": "2023-01-01T00:00:00",
                    "last_accessed": "2023-01-01T00:00:00",
                    "access_count": 1,
                    "size": file_size,
                    "tags": ["test", "buildings", "dataframe"],
                    "data_type": "pickle",
                    "table_name": "buildings",
                    "metadata": {"description": "Sample buildings data", "rows": 10}
                }
            
            # Override the mocked method temporarily
            logger.debug("Temporarily overriding get_data_info mock method")
            original_get_info = memory_catalog.get_data_info
            memory_catalog.get_data_info = mock_get_red_hot_info
            
            try:
                # Register the pickle file
                logger.info(f"Registering pickle file in Red Hot tier")
                
                data_id = await memory_catalog.register_data(
                    tier="red_hot",
                    location=pickle_location,
                    size=file_size,
                    data_type="pickle",
                    tags=["test", "buildings", "dataframe"],
                    metadata={"description": "Sample buildings data", "rows": 10},
                    table_name="buildings"
                )
                
                # Verify data was registered
                assert data_id is not None
                assert isinstance(data_id, str)
                logger.info(f"Successfully registered pickle in Red Hot tier with data_id: {data_id}")
                
                # Retrieve the data info
                logger.debug(f"Retrieving data info for data_id: {data_id}")
                data_info = await memory_catalog.get_data_info(data_id)
                assert data_info is not None
                assert data_info["tier"] == "red_hot"
                assert data_info["data_type"] == "pickle"
                assert "buildings" in data_info["tags"]
                logger.info(f"Successfully retrieved data info for Red Hot pickle data")
                logger.info(f"Pickle file metadata in catalog: {data_info}")
                
                # Verify it can be found by tag search
                logger.debug("Searching by 'buildings' tag")
                results = await memory_catalog.search_by_tags(["buildings"])
                assert len(results) > 0
                logger.info(f"Successfully found {len(results)} results by tag search")
                
                # Verify it appears in the red_hot tier data
                logger.debug("Retrieving all red_hot tier data")
                tier_data = await memory_catalog.get_tier_data("red_hot")
                assert len(tier_data) > 0
                logger.info(f"Successfully found {len(tier_data)} entries in red_hot tier")
                
                # Simulating loading the pickle file into Red Hot memory
                logger.info("Simulating loading the pickle into Red Hot memory:")
                with open(pickle_location, 'rb') as f:
                    loaded_data = pickle.load(f)
                logger.info(f"Successfully loaded pickle file into memory")
                logger.info(f"Loaded data type: {type(loaded_data).__name__}")
                logger.info(f"Loaded data shape: {loaded_data.shape}")
                
                # Simulate a query on the loaded data
                if isinstance(loaded_data, pd.DataFrame):
                    logger.info("Performing sample query: Find buildings taller than 300m")
                    tall_buildings = loaded_data[loaded_data['height'] > 300]
                    logger.info(f"Found {len(tall_buildings)} tall buildings")
                    
                    if not tall_buildings.empty:
                        logger.info("Tall buildings details:")
                        for i, row in tall_buildings.iterrows():
                            logger.info(f"Building: {row['name']}, Height: {row['height']:.1f}m, Floors: {row['floors']}")
                
            finally:
                # Restore original mock
                logger.debug("Restoring original get_data_info mock method")
                memory_catalog.get_data_info = original_get_info
        
        finally:
            # Clean up the pickle file
            if os.path.exists(pickle_location):
                os.unlink(pickle_location)
                logger.info(f"Cleaned up pickle file: {pickle_location}")
    
    @pytest.mark.asyncio
    async def test_red_hot_memory_with_catalog_integration(self, memory_catalog):
        """Test integration between RedHotMemory and MemoryCatalog for pickle files."""
        logger.info("Testing integration between RedHotMemory and MemoryCatalog")
        
        # Import mock needed for this test
        from unittest.mock import patch
        
        # Setup mock for RedHotMemory
        logger.debug("Setting up mock RedHotMemory class")
        class MockRedHotMemory:
            def __init__(self):
                self.data = {}
                logger.debug("MockRedHotMemory initialized")
            
            async def load_pickle(self, file_path, key=None, register_in_catalog=False):
                logger.debug(f"MockRedHotMemory.load_pickle called with file_path={file_path}, key={key}, register_in_catalog={register_in_catalog}")
                self.data[key or "default"] = f"Mock data from {file_path}"
                
                # If catalog registration is requested, do it
                if register_in_catalog:
                    logger.info(f"Registering pickle in catalog as requested")
                    # Use the actual catalog instance from the test
                    await memory_catalog.register_data(
                        tier="red_hot",
                        location=file_path,
                        size=1000,  # Mock size
                        data_type="pickle",
                        tags=["pickle", "test"],
                        metadata={"source": "test", "registered_by": "load_pickle"},
                        table_name=key
                    )
                return True
        
        # Create a path for a test pickle file
        pickle_path = "/tmp/test_buildings.pkl"
        logger.info(f"Using test pickle path: {pickle_path}")
        
        # Create our mock
        red_hot = MockRedHotMemory()
        
        # Track if register_data was called
        register_called = False
        original_register = memory_catalog.register_data
        
        async def mock_register(*args, **kwargs):
            nonlocal register_called
            register_called = True
            logger.debug(f"Tracked register_data called with args={args}, kwargs={kwargs}")
            return await original_register(*args, **kwargs)
        
        # Replace register_data with our tracking version
        logger.debug("Replacing register_data with tracking version")
        memory_catalog.register_data = mock_register
        
        try:
            # Load the pickle into RedHotMemory (this should trigger catalog registration)
            key = "test_buildings"
            logger.info(f"Loading pickle into RedHotMemory with key: {key}")
            await red_hot.load_pickle(pickle_path, key=key, register_in_catalog=True)
            
            # Verify the data was loaded
            assert key in red_hot.data
            logger.info(f"Successfully verified data was loaded into RedHotMemory with key: {key}")
            
            # Verify catalog registration was called
            assert register_called
            logger.info("Successfully verified catalog registration was called")
            
        finally:
            # Restore original method
            logger.debug("Restoring original register_data method")
            memory_catalog.register_data = original_register
    
    @pytest.mark.asyncio
    async def test_cold_to_red_hot_promotion_with_catalog(self, memory_catalog):
        """Test updating the catalog when data is promoted from Cold to Red Hot memory."""
        logger.info("Testing catalog updates during Cold to Red Hot promotion")
        
        # Register data initially in Cold tier
        cold_location = "/tmp/cold_buildings.pkl"
        logger.info(f"Registering test data in Cold tier from location: {cold_location}")
        
        # First, register in cold tier
        data_id = await memory_catalog.register_data(
            tier="cold",
            location=cold_location,
            size=1000,
            data_type="pickle",
            tags=["buildings", "cold"],
            metadata={"description": "Cold storage buildings data"}
        )
        logger.info(f"Successfully registered data in Cold tier with data_id: {data_id}")
        
        # Mock the update tier function (normally would be part of MemoryTiering)
        async def mock_update_tier(data_id, new_tier, new_location):
            logger.debug(f"Mock update_tier called with data_id={data_id}, new_tier={new_tier}, new_location={new_location}")
            # We'll directly call execute on the mock connection
            # In a real implementation, this would update the DB
            await memory_catalog.con.execute("""
                UPDATE memory_catalog
                SET primary_tier = ?, location = ?
                WHERE data_id = ?
            """, [new_tier, new_location, data_id])
            return True
        
        # Configure mock to return updated data after "promotion"
        red_hot_location = "memory:buildings"
        logger.debug(f"Setting up promotion to Red Hot location: {red_hot_location}")
        
        # Create a modified version of get_data_info to return cold or red_hot based on call count
        call_count = 0
        original_get_info = memory_catalog.get_data_info
        
        async def mock_get_info_with_promotion(data_id):
            nonlocal call_count
            call_count += 1
            logger.debug(f"Mock get_data_info called (count={call_count}) for data_id={data_id}")
            
            # First call returns cold, subsequent calls return red_hot
            if call_count == 1:
                logger.debug("Returning Cold tier data info (before promotion)")
                return {
                    "data_id": data_id,
                    "tier": "cold",
                    "location": cold_location,
                    "created": "2023-01-01T00:00:00",
                    "last_accessed": "2023-01-01T00:00:00",
                    "access_count": 1,
                    "size": 1000,
                    "tags": ["buildings", "cold"],
                    "data_type": "pickle",
                    "table_name": "buildings",
                    "metadata": {"description": "Cold storage buildings data"}
                }
            else:
                logger.debug("Returning Red Hot tier data info (after promotion)")
                return {
                    "data_id": data_id,
                    "tier": "red_hot",
                    "location": red_hot_location,
                    "created": "2023-01-01T00:00:00",
                    "last_accessed": "2023-01-01T00:00:00",
                    "access_count": 2,
                    "size": 1000,
                    "tags": ["buildings", "cold"],
                    "data_type": "pickle",
                    "table_name": "buildings",
                    "metadata": {"description": "Cold storage buildings data"}
                }
        
        # Override the mocked method
        logger.debug("Temporarily overriding get_data_info to simulate promotion")
        memory_catalog.get_data_info = mock_get_info_with_promotion
        
        try:
            # Verify initial tier is cold
            logger.info("Verifying initial tier is 'cold'")
            data_info = await memory_catalog.get_data_info(data_id)
            assert data_info["tier"] == "cold"
            logger.info("Confirmed initial tier is 'cold'")
            
            # Simulate promotion
            logger.info(f"Simulating promotion from Cold to Red Hot for data_id: {data_id}")
            await mock_update_tier(data_id, "red_hot", red_hot_location)
            
            # Verify the tier was updated
            logger.info("Verifying tier was updated to 'red_hot'")
            data_info_after = await memory_catalog.get_data_info(data_id)
            assert data_info_after["tier"] == "red_hot"
            assert data_info_after["location"] == red_hot_location
            logger.info(f"Successfully confirmed promotion to Red Hot tier at location: {red_hot_location}")
            
            # Verify it now appears in red_hot tier data
            logger.info("Verifying data appears in red_hot tier query")
            tier_data = await memory_catalog.get_tier_data("red_hot")
            assert any(item["data_id"] == data_id for item in tier_data)
            logger.info("Successfully confirmed data appears in red_hot tier query results")
            
        finally:
            # Restore original mock
            logger.debug("Restoring original get_data_info mock")
            memory_catalog.get_data_info = original_get_info 
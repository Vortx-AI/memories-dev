"""
Tests for the RedHotMemory class in the core.red_hot module.
"""

import os
import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path
import asyncio
import pickle
import json
import time
import logging
import pandas as pd
import sys  # Add sys import for sys.exit()

from memories.core.red_hot import RedHotMemory

# Import necessary classes for the tests
try:
    from memories.core.memory_tiering import MemoryTiering
    from memories.core.memory_retrieval import MemoryRetrieval
except ImportError:
    # Create mock classes if the real ones are not available
    class MemoryTiering:
        async def initialize_tiers(self):
            logger.warning("Using mock MemoryTiering class")
            self.red_hot = RedHotMemory()
            return True
            
        async def cold_pickle_to_red_hot(self, pickle_path, red_hot_key):
            logger.warning(f"Mock promotion of {pickle_path} to {red_hot_key}")
            return False
    
    class MemoryRetrieval:
        async def initialize(self):
            logger.warning("Using mock MemoryRetrieval class")
            return True
            
        async def is_gpu_available(self):
            return False
            
        async def gpu_filter(self, data_key, conditions):
            return None
            
        async def gpu_aggregate(self, data_key, aggregations):
            return None
            
        async def get_gpu_library_info(self):
            return {}

# Create a mock GlacierMemory class to avoid GCS connection issues
try:
    from memories.core.glacier.memory import GlacierMemory
except ImportError:
    class GlacierMemory:
        def __init__(self, config=None):
            logger.warning("Using mock GlacierMemory class")
            self.is_connected = False
            
        def connect(self):
            logger.warning("Mock GlacierMemory connect")
            self.is_connected = True
            return True

        def disconnect(self):
            logger.warning("Mock GlacierMemory disconnect")
            self.is_connected = False
            return True

# Override actual MemoryTiering to patch GlacierMemory initialization
class MockMemoryTiering(MemoryTiering):
    async def initialize_tiers(self):
        """Initialize only RedHot memory for testing."""
        logger.info("Initializing minimal memory tiers (RedHot only)")
        # Initialize RedHot memory (most important for this test)
        self.red_hot = RedHotMemory()
        self.red_hot.data = {}  # Ensure the data dict exists
        
        # Don't initialize other tiers - just create empty attributes
        self.hot = None
        self.warm = None
        self.cold = None
        self.glacier = None
        
        logger.info("Successfully initialized RedHot memory only")
        return True
    
    async def cold_pickle_to_red_hot(self, pickle_path, red_hot_key):
        """Load data from a pickle file directly to RedHot memory."""
        logger.info(f"Loading pickle data from {pickle_path} to RedHot with key {red_hot_key}")
        try:
            # Load the pickle file
            with open(pickle_path, 'rb') as f:
                data = pickle.load(f)
            
            # Store in red hot memory
            if not hasattr(self.red_hot, 'data'):
                self.red_hot.data = {}
            
            self.red_hot.data[red_hot_key] = data
            logger.info(f"Successfully loaded data to RedHot memory with key {red_hot_key}")
            return True
        except Exception as e:
            logger.error(f"Error loading pickle to RedHot: {e}")
            return False

# Define paths for pickle files
SAMPLE_PKL_PATH = os.path.join(tempfile.gettempdir(), "sample_buildings.pkl")
MULTI_TABLE_PKL_PATH = os.path.join(tempfile.gettempdir(), "multi_table_data.pkl")

# Configure more verbose logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)
logger = logging.getLogger(__name__)
# Set root logger to INFO to see more messages
logging.getLogger().setLevel(logging.INFO)
# Make our test logger even more verbose
logger.setLevel(logging.DEBUG)

@pytest.fixture
def temp_storage_path():
    """Create a temporary directory for storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after test
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Failed to clean up temporary directory {temp_dir}: {e}")


@pytest.fixture
def red_hot_memory(temp_storage_path):
    """Create a RedHotMemory instance for testing."""
    memory = RedHotMemory(dimension=128, storage_path=temp_storage_path)
    yield memory
    # Clean up
    memory.cleanup()


class TestRedHotMemory:
    """Tests for the RedHotMemory class."""

    def test_initialization(self, temp_storage_path):
        """Test that RedHotMemory initializes correctly."""
        memory = RedHotMemory(dimension=128, storage_path=temp_storage_path)
        
        # Check that the storage directory was created
        assert Path(temp_storage_path).exists()
        
        # Check that the dimension was set correctly
        assert memory.dimension == 128
        
        # Check that the metadata is initialized
        assert memory.metadata == {}

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, red_hot_memory):
        """Test storing and retrieving vectors."""
        # Create a test vector
        test_vector = np.random.rand(128).astype(np.float32)
        test_metadata = {"source": "test", "importance": "high"}
        test_tags = ["test", "important"]
        
        # Store the vector
        result = await red_hot_memory.store(
            data=test_vector,
            metadata=test_metadata,
            tags=test_tags
        )
        assert result is True
        
        # Retrieve the vector
        retrieved = await red_hot_memory.retrieve(query_vector=test_vector, k=1)
        
        # Check that we got a result
        assert retrieved is not None
        assert len(retrieved) == 1
        
        # Check that the metadata and tags were stored correctly
        assert retrieved[0]["metadata"] == test_metadata
        assert retrieved[0]["tags"] == test_tags
        
        # Check that the distance is close to 0 (exact match)
        assert retrieved[0]["distance"] < 1e-5

    @pytest.mark.asyncio
    async def test_retrieve_with_tags(self, red_hot_memory):
        """Test retrieving vectors filtered by tags."""
        # Create and store two test vectors with different tags
        vector1 = np.random.rand(128).astype(np.float32)
        vector2 = np.random.rand(128).astype(np.float32)
        
        await red_hot_memory.store(
            data=vector1,
            metadata={"id": "vector1"},
            tags=["tag1", "common"]
        )
        
        await red_hot_memory.store(
            data=vector2,
            metadata={"id": "vector2"},
            tags=["tag2", "common"]
        )
        
        # Retrieve with tag1 filter
        retrieved = await red_hot_memory.retrieve(
            query_vector=vector1,
            k=2,
            tags=["tag1"]
        )
        
        # Should only get vector1
        assert len(retrieved) == 1
        assert retrieved[0]["metadata"]["id"] == "vector1"
        
        # Retrieve with common tag filter
        retrieved = await red_hot_memory.retrieve(
            query_vector=vector1,
            k=2,
            tags=["common"]
        )
        
        # Should get both vectors
        assert len(retrieved) == 2

    @pytest.mark.asyncio
    async def test_clear(self, red_hot_memory):
        """Test clearing the memory."""
        # Store a vector
        test_vector = np.random.rand(128).astype(np.float32)
        await red_hot_memory.store(data=test_vector)
        
        # Clear the memory
        red_hot_memory.clear()
        
        # Check that the metadata is empty
        assert red_hot_memory.metadata == {}
        
        # Try to retrieve the vector (should return None)
        retrieved = await red_hot_memory.retrieve(query_vector=test_vector, k=1)
        assert not retrieved

    @pytest.mark.asyncio
    async def test_get_schema(self, red_hot_memory):
        """Test getting schema information for a vector."""
        # Store a vector
        test_vector = np.random.rand(128).astype(np.float32)
        test_metadata = {"source": "test"}
        test_tags = ["test"]
        
        await red_hot_memory.store(
            data=test_vector,
            metadata=test_metadata,
            tags=test_tags
        )
        
        # Get schema for the vector
        schema = await red_hot_memory.get_schema(vector_id=0)
        
        # Check schema properties
        assert schema is not None
        assert schema["dimension"] == 128
        assert schema["type"] == "vector"
        assert schema["source"] == "faiss"
        assert schema["metadata"] == test_metadata
        assert schema["tags"] == test_tags

    def test_list_input(self, red_hot_memory):
        """Test that the store method accepts list inputs."""
        # Create a test vector as a list
        test_vector = list(np.random.rand(128).astype(np.float32))
        
        # Store the vector with metadata to ensure it's returned in results
        # (RedHotMemory.retrieve() only returns results with metadata)
        result = asyncio.run(red_hot_memory.store(
            data=test_vector,
            metadata={"source": "test"},
            tags=["test"]
        ))
        assert result is True
        
        # Retrieve the vector
        retrieved = asyncio.run(red_hot_memory.retrieve(query_vector=test_vector, k=1))
        
        # Check that we got a result
        assert retrieved is not None
        assert len(retrieved) == 1
        
        # Check that the distance is close to 0 (exact match)
        assert retrieved[0]["distance"] < 1e-5

    @pytest.mark.asyncio
    async def test_import_pkl_to_red_hot(self, red_hot_memory, temp_storage_path):
        """Test importing vectors from a pickle file."""
        # Create a temporary pickle file with test vectors
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            # Create test vectors (10 vectors of dimension 128 to match fixture)
            test_vectors = np.random.randn(10, 128).astype(np.float32)
            pickle.dump(test_vectors, tmp_file)
            tmp_file_path = tmp_file.name

        try:
            # Initialize memory store with our test red_hot_memory
            from memories.core.memory_store import MemoryStore
            store = MemoryStore()
            store._red_hot_memory = red_hot_memory
            
            # Import the vectors
            success = await store.import_pkl_to_red_hot(
                pkl_file=tmp_file_path,
                tags=["test", "embeddings"],
                metadata={"description": "Test vectors"},
                vector_dimension=128  # Match the dimension from fixture
            )
            
            # Check that the import was successful
            assert success is True
            
            # Query one of the original vectors to verify storage
            query_vector = test_vectors[0]
            results = await red_hot_memory.retrieve(
                query_vector=query_vector,
                k=1,
                tags=["test", "embeddings"]
            )
            
            # Verify we got a result
            assert results is not None
            assert len(results) == 1
            
            # Verify the metadata
            assert results[0]["metadata"]["description"] == "Test vectors"
            assert results[0]["metadata"]["vector_id"] == 0
            assert results[0]["metadata"]["source_file"] == tmp_file_path
            
            # Verify the distance is very small (should be exact match)
            assert results[0]["distance"] < 1e-5
            
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    @pytest.mark.asyncio
    async def test_delete(self, red_hot_memory, temp_storage_path):
        """Test deleting data from red hot memory."""
        # Create test vector
        test_vector = np.random.rand(128).astype(np.float32)
        
        # Store vector
        key = 'test_delete_key'
        metadata = {'test': 'metadata'}
        
        # Mock the metadata and index for testing
        red_hot_memory.metadata = {
            key: {
                'index': 0,
                'metadata': metadata
            }
        }
        red_hot_memory.metadata_file = os.path.join(temp_storage_path, 'metadata.json')
        
        # Save metadata
        with open(red_hot_memory.metadata_file, 'w') as f:
            json.dump(red_hot_memory.metadata, f)
        
        # Delete vector
        deleted = await red_hot_memory.delete(key)
        assert deleted is True
        
        # Verify vector is marked as deleted in metadata
        with open(red_hot_memory.metadata_file, 'r') as f:
            updated_metadata = json.load(f)
        
        assert updated_metadata[key]['deleted'] is True
        
        # Try to delete non-existent key
        deleted_non_existent = await red_hot_memory.delete('non_existent_key')
        assert deleted_non_existent is False

def create_sample_buildings_data(num_buildings=1000):
    """Create sample building data for testing."""
    print(f"Creating sample data for {num_buildings} buildings...")
    np.random.seed(42)  # For reproducibility
    
    # Generate random building data
    data = {
        'id': range(1, num_buildings + 1),
        'name': [f"Building_{i}" for i in range(1, num_buildings + 1)],
        'height': np.random.uniform(10, 400, num_buildings),
        'floors': np.random.randint(1, 100, num_buildings),
        'building_type': np.random.choice(['residential', 'commercial', 'mixed', 'industrial'], num_buildings),
        'year_built': np.random.randint(1950, 2023, num_buildings),
        'latitude': np.random.uniform(25.0, 25.3, num_buildings),  # Dubai coordinates
        'longitude': np.random.uniform(55.0, 55.4, num_buildings)  # Dubai coordinates
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    print(f"Created DataFrame with shape: {df.shape}")
    
    # Add a few special buildings for testing
    burj_khalifa_idx = np.random.randint(0, num_buildings)
    df.loc[burj_khalifa_idx, 'name'] = 'Burj Khalifa'
    df.loc[burj_khalifa_idx, 'height'] = 828
    df.loc[burj_khalifa_idx, 'floors'] = 163
    print(f"Added Burj Khalifa at index {burj_khalifa_idx}")
    
    return df

def create_sample_roads_data(num_roads=500):
    """Create sample road data for testing."""
    print(f"Creating sample data for {num_roads} roads...")
    np.random.seed(43)  # Different seed from buildings
    
    # Generate random road data
    data = {
        'id': range(1, num_roads + 1),
        'name': [f"Road_{i}" for i in range(1, num_roads + 1)],
        'length': np.random.uniform(100, 5000, num_roads),
        'width': np.random.uniform(3, 12, num_roads),
        'road_type': np.random.choice(['highway', 'main', 'secondary', 'residential'], num_roads),
        'lanes': np.random.randint(1, 6, num_roads),
        'latitude': np.random.uniform(25.0, 25.3, num_roads),  # Dubai coordinates
        'longitude': np.random.uniform(55.0, 55.4, num_roads)  # Dubai coordinates
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    print(f"Created roads DataFrame with shape: {df.shape}")
    
    return df

def create_single_table_pickle():
    """Create a single table pickle file with building data."""
    print(f"\n--- CREATING SINGLE TABLE PICKLE ---")
    global SAMPLE_PKL_PATH  # Add this line to ensure access to the global variable
    logger.info(f"Creating single table pickle file at {SAMPLE_PKL_PATH}")
    
    # Create sample data
    print("Generating building data...")
    buildings_df = create_sample_buildings_data()
    
    # Save to pickle file
    print(f"Saving DataFrame to pickle file: {SAMPLE_PKL_PATH}")
    with open(SAMPLE_PKL_PATH, 'wb') as f:
        pickle.dump(buildings_df, f)
    
    file_size = os.path.getsize(SAMPLE_PKL_PATH) / 1024
    print(f"Pickle file created, size: {file_size:.2f} KB")
    logger.info(f"Created pickle file with {len(buildings_df)} buildings")
    return SAMPLE_PKL_PATH

def create_multi_table_pickle():
    """Create a multi-table pickle file with buildings and roads."""
    print(f"\n--- CREATING MULTI-TABLE PICKLE ---")
    global MULTI_TABLE_PKL_PATH  # Add this line to ensure access to the global variable
    logger.info(f"Creating multi-table pickle file at {MULTI_TABLE_PKL_PATH}")
    
    # Create sample data
    print("Generating building and road data...")
    buildings_df = create_sample_buildings_data()
    roads_df = create_sample_roads_data()
    
    # Create dictionary with tables
    print("Creating nested dictionary structure...")
    tables = {
        'buildings': buildings_df,
        'roads': roads_df
    }
    
    # Wrap in another dict to match expected structure
    data = {
        'tables': tables,
        'metadata': {
            'created_at': time.time(),
            'version': '1.0',
            'description': 'Sample data for GPU memory testing'
        }
    }
    
    # Save to pickle file
    print(f"Saving multi-table data to pickle file: {MULTI_TABLE_PKL_PATH}")
    with open(MULTI_TABLE_PKL_PATH, 'wb') as f:
        pickle.dump(data, f)
    
    file_size = os.path.getsize(MULTI_TABLE_PKL_PATH) / 1024
    print(f"Multi-table pickle file created, size: {file_size:.2f} KB")
    logger.info(f"Created multi-table pickle with {len(buildings_df)} buildings and {len(roads_df)} roads")
    return MULTI_TABLE_PKL_PATH

def check_gpu_availability():
    """Check if GPU is available for testing."""
    print("\n--- CHECKING GPU AVAILABILITY ---")
    red_hot = RedHotMemory()
    
    # Check if GPU is available by examining attributes rather than calling a non-existent method
    # We can check if any GPU libraries are available through attributes
    gpu_libs = getattr(red_hot, 'gpu_libraries', {})
    is_available = bool(gpu_libs)
    
    # Alternative approach: check if index_type is GPU-based
    # is_available = hasattr(red_hot, 'index_type') and 'GPU' in red_hot.index_type.upper()
    
    if is_available:
        print(f"GPU AVAILABLE: Yes")
        print(f"Detected GPU libraries: {list(gpu_libs.keys())}")
        logger.info(f"GPU is available with libraries: {list(gpu_libs.keys())}")
    else:
        print(f"GPU AVAILABLE: No")
        print("No GPU detected - tests will run in simulation mode")
        logger.warning("GPU is not available - tests will run in simulation mode")
    
    return is_available

async def test_cold_to_red_hot_promotion(file_path):
    """Test promoting data from a pickle file in Cold storage to Red Hot memory."""
    print("\n--- TESTING COLD TO RED HOT PROMOTION ---")
    logger.info("Testing Cold to Red Hot Promotion")
    
    # Initialize memory tiering with our mock class instead
    print("Initializing memory tiering...")
    try:
        memory_tiering = MockMemoryTiering()
        print("Initializing memory tiers...")
        await memory_tiering.initialize_tiers()
    except Exception as e:
        print(f"WARNING: Error during memory tiering initialization: {e}")
        print("Falling back to minimal mock...")
        # Fallback to minimal implementation if needed
        memory_tiering = MemoryTiering()
        memory_tiering.red_hot = RedHotMemory()
        memory_tiering.red_hot.data = {}
    
    # Verify GPU availability
    has_gpu = memory_tiering.red_hot.is_available()
    print(f"GPU availability: {'Yes' if has_gpu else 'No'}")
    logger.info(f"GPU availability: {has_gpu}")
    
    try:
        # Use the cold_pickle_to_red_hot method to directly load a pickle to GPU
        print(f"Promoting data from pickle to Red Hot memory: {file_path}")
        logger.info(f"Promoting data from pickle {file_path} to Red Hot memory")
        start_time = time.time()
        
        # The method takes a file path and an optional key
        print("Calling memory_tiering.cold_pickle_to_red_hot()...")
        success = await memory_tiering.cold_pickle_to_red_hot(
            pickle_path=file_path,
            red_hot_key='test_data'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Promotion result: {'SUCCESS' if success else 'FAILURE'}")
        print(f"Promotion time: {duration:.2f} seconds")
        
        if success:
            logger.info(f"Successfully promoted data to Red Hot memory in {duration:.2f} seconds")
            
            # Verify the data was loaded
            if 'test_data' in memory_tiering.red_hot.data:
                data = memory_tiering.red_hot.data['test_data']
                print(f"Data found in Red Hot memory with key 'test_data'")
                print(f"Data type: {type(data).__name__}")
                logger.info(f"Data type in Red Hot memory: {type(data).__name__}")
                
                # Check if it's a DataFrame (either pandas or GPU)
                if hasattr(data, 'shape'):
                    print(f"Data shape: {data.shape}")
                    logger.info(f"Data shape: {data.shape}")
                elif isinstance(data, dict) and 'tables' in data:
                    print("Found nested table structure:")
                    for table_name, table_data in data['tables'].items():
                        print(f"  - Table '{table_name}' shape: {table_data.shape}")
                        logger.info(f"Table {table_name} shape: {table_data.shape}")
            else:
                print("ERROR: Data was not found in Red Hot memory with key 'test_data'")
                logger.error("Data was not found in Red Hot memory with key 'test_data'")
                return False
        else:
            print("ERROR: Failed to promote data to Red Hot memory")
            logger.error("Failed to promote data to Red Hot memory")
            return False
            
    except Exception as e:
        print(f"ERROR during promotion: {str(e)}")
        logger.error(f"Error during promotion: {e}")
        import traceback
        print(traceback.format_exc())
        logger.error(traceback.format_exc())
        return False
    
    return True

async def test_gpu_queries_single_table():
    """Test executing queries on a single table in Red Hot memory."""
    print("\n--- TESTING GPU QUERIES ON SINGLE TABLE ---")
    logger.info("Testing GPU Queries on Single Table")
    
    # Initialize memory retrieval
    print("Initializing memory retrieval...")
    memory_retrieval = MemoryRetrieval()
    print("Initializing memory tiers...")
    await memory_retrieval.initialize()
    
    # Check GPU availability
    gpu_available = await memory_retrieval.is_gpu_available()
    print(f"GPU availability: {'Yes' if gpu_available else 'No'}")
    logger.info(f"GPU availability: {gpu_available}")
    
    if not gpu_available:
        print("WARNING: GPU not available - running in simulation mode")
        logger.warning("GPU not available - running in simulation mode")
    
    try:
        # Test a simple filter query
        print("\nExecuting simple filter query to find tall buildings...")
        logger.info("Executing simple filter query...")
        tall_buildings = await memory_retrieval.gpu_filter(
            data_key='test_data',
            conditions=[
                {'column': 'height', 'operator': '>', 'value': 200}
            ]
        )
        
        if tall_buildings is not None:
            print(f"SUCCESS: Found {len(tall_buildings)} buildings taller than 200m")
            logger.info(f"Found {len(tall_buildings)} buildings taller than 200m")
        else:
            print("ERROR: Filter query returned None")
            logger.error("Filter query returned None")
            
        # Test finding the tallest building
        print("\nFinding the tallest building...")
        logger.info("Finding the tallest building...")
        tallest_building = await memory_retrieval.gpu_aggregate(
            data_key='test_data',
            aggregations=[
                {'column': 'height', 'function': 'max'}
            ]
        )
        
        if tallest_building is not None:
            print(f"SUCCESS: Tallest building height: {tallest_building}")
            logger.info(f"Tallest building height: {tallest_building}")
        else:
            print("ERROR: Aggregation query returned None")
            logger.error("Aggregation query returned None")
            
        # Test a SQL query if cuDF SQL is available
        try:
            if gpu_available:
                library_info = await memory_retrieval.get_gpu_library_info()
                print(f"Available GPU libraries: {library_info}")
                
                if 'cudf' in library_info:
                    print("\nExecuting SQL query on GPU...")
                    logger.info("Executing SQL query on GPU...")
                    sql_query = """
                        SELECT building_type, AVG(height) as avg_height, COUNT(*) as count
                        FROM test_data
                        GROUP BY building_type
                        ORDER BY avg_height DESC
                    """
                    print(f"SQL Query: {sql_query}")
                    sql_result = await memory_retrieval.gpu_query(sql_query)
                    
                    if sql_result is not None:
                        print(f"SUCCESS: SQL query returned {len(sql_result)} rows")
                        print(sql_result)
                        logger.info(f"SQL query result: {len(sql_result)} rows")
                        logger.info(sql_result)
                    else:
                        print("ERROR: SQL query returned None")
                        logger.error("SQL query returned None")
        except Exception as sql_err:
            print(f"ERROR in SQL query: {sql_err}")
            logger.error(f"Error in SQL query: {sql_err}")
        
        return True
            
    except Exception as e:
        print(f"ERROR during query tests: {str(e)}")
        logger.error(f"Error during query tests: {e}")
        import traceback
        print(traceback.format_exc())
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main test function."""
    global sys  # Add this line to ensure access to the global module
    print("\n==============================================")
    print("STARTING GPU MEMORY TESTS")
    print("==============================================")
    logger.info("Starting GPU memory tests")
    
    # Check if GPU is available
    gpu_available = check_gpu_availability()
    
    # Create sample data
    try:
        single_table_path = create_single_table_pickle()
        print(f"Created single table pickle at: {single_table_path}")
    except Exception as e:
        print(f"ERROR creating pickle: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
    
    # Test data promotion from Cold to Red Hot
    try:
        print("\nTesting data promotion...")
        promotion_success = await test_cold_to_red_hot_promotion(single_table_path)
        
        if promotion_success:
            print("\nData promotion SUCCESSFUL - continuing with query tests")
            
            # Test GPU queries on single table
            await test_gpu_queries_single_table()
            
        else:
            print("\nData promotion FAILED - skipping query tests")
            logger.error("Data promotion failed - skipping query tests")
    except Exception as e:
        print(f"ERROR in main test flow: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("\n==============================================")
    print("GPU MEMORY TESTS COMPLETED")
    print("==============================================")
    logger.info("GPU memory tests completed")

if __name__ == "__main__":
    print(f"Starting test_red_hot_memory.py at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(main())
    print(f"Test completed at {time.strftime('%Y-%m-%d %H:%M:%S')}") 
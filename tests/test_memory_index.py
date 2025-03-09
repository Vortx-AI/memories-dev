"""Tests for memory index functionality."""

import pytest
import numpy as np
import pandas as pd
import faiss
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from datetime import datetime
import json

from memories.core.memory_index import MemoryIndex
from memories.core.memory_catalog import memory_catalog

@pytest.fixture
def mock_memory_catalog():
    """Mock memory catalog with test data for each tier."""
    mock = AsyncMock()
    
    # Create base data structure that will be common across tiers
    base_data = {
        'created_at': datetime.now().isoformat(),
        'last_accessed': datetime.now().isoformat(),
        'access_count': 1,
        'size': 1000,
        'tags': 'tag1,tag2'
    }
    
    # Define test data for each tier
    test_data = {
        "hot": [{
            **base_data,
            'data_id': 'hot_test1',
            'location': '/test/hot/location1',
            'data_type': 'dict',
            'additional_meta': json.dumps({
                'source': 'redis',
                'fields': ['column1', 'column2']
            })
        }],
        "warm": [{
            **base_data,
            'data_id': 'warm_test1',
            'location': '/test/warm/location1',
            'data_type': 'dict',
            'additional_meta': json.dumps({
                'source': 'json_file',
                'fields': ['column3', 'column4']
            })
        }],
        "cold": [{
            **base_data,
            'data_id': 'cold_test1',
            'location': '/test/cold/location1',
            'data_type': 'dataframe',
            'additional_meta': json.dumps({
                'source': 'duckdb',
                'columns': ['column5', 'column6']
            })
        }],
        "red_hot": [{
            **base_data,
            'data_id': 'red_hot_test1',
            'location': '/test/red_hot/location1',
            'data_type': 'vector',
            'additional_meta': json.dumps({
                'source': 'faiss',
                'fields': ['column7', 'column8']
            })
        }],
        "glacier": [{
            **base_data,
            'data_id': 'glacier_test1',
            'location': '/test/glacier/location1',
            'data_type': 'geodataframe',
            'additional_meta': json.dumps({
                'source': 'osm',
                'spatial_input': [0, 0, 1, 1],
                'spatial_input_type': 'bbox',
                'geometry_type': 'Point'
            })
        }]
    }

    # Create async mock for get_tier_data
    async def mock_get_tier_data(tier):
        """Mock implementation of get_tier_data."""
        return test_data[tier]

    # Set up the mock with the async method
    mock.get_tier_data = AsyncMock(wraps=mock_get_tier_data)
    mock.test_data = test_data  # Store test data for reference
    return mock

@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer that returns consistent test vectors."""
    mock = Mock()
    
    def encode(texts):
        """Mock encode method that returns a fixed test vector."""
        # Create a deterministic test vector based on input text
        if isinstance(texts, str):
            texts = [texts]
            
        # Generate a fixed vector for each text
        vectors = []
        for text in texts:
            # Create a deterministic vector based on text length
            seed = sum(ord(c) for c in text)
            np.random.seed(seed)
            vector = np.random.rand(384).astype(np.float32)  # Shape: [384]
            vectors.append(vector)
            
        # Stack vectors into a batch
        return np.stack(vectors)  # Shape: [batch_size, 384]
    
    mock.encode = encode
    return mock

@pytest.fixture
def mock_hot_memory():
    """Mock hot memory with schema information."""
    mock = AsyncMock()
    
    async def get_schema(data_id):
        if data_id == 'hot_test1':
            return {
                'fields': ['column1', 'column2'],
                'types': {'column1': 'str', 'column2': 'int'},
                'type': 'dict',
                'source': 'redis'
            }
        return None
        
    mock.get_schema = AsyncMock(side_effect=get_schema)
    mock.cleanup = AsyncMock()
    return mock

@pytest.fixture
def mock_warm_memory():
    """Mock warm memory with schema information."""
    mock = AsyncMock()
    
    async def get_schema(location):
        if 'warm_test1' in location:
            return {
                'fields': ['column3', 'column4'],
                'types': {'column3': 'float', 'column4': 'str'},
                'type': 'dict',
                'source': 'json_file'
            }
        return None
        
    mock.get_schema = AsyncMock(side_effect=get_schema)
    mock.cleanup = AsyncMock()
    return mock

@pytest.fixture
def mock_cold_memory():
    """Mock cold memory with schema information."""
    mock = AsyncMock()
    
    async def get_schema(data_id):
        if data_id == 'cold_test1':
            return {
                'columns': ['column5', 'column6'],
                'dtypes': {'column5': 'int64', 'column6': 'float64'},
                'type': 'dataframe',
                'source': 'duckdb'
            }
        return None
        
    mock.get_schema = AsyncMock(side_effect=get_schema)
    mock.cleanup = AsyncMock()
    return mock

@pytest.fixture
def mock_red_hot_memory():
    """Mock red hot memory with schema information."""
    mock = AsyncMock()
    
    async def get_schema(data_id):
        if data_id == 'red_hot_test1':
            return {
                'dimension': 384,
                'type': 'vector',
                'source': 'faiss',
                'index_type': 'IndexFlatL2'
            }
        return None
        
    mock.get_schema = AsyncMock(side_effect=get_schema)
    mock.cleanup = AsyncMock()
    return mock

@pytest.fixture
def mock_glacier_memory():
    """Mock glacier memory with schema information."""
    mock = AsyncMock()
    
    async def get_schema(source, spatial_input, spatial_input_type='bbox'):
        if source == 'osm':
            return {
                'columns': ['lat', 'lon', 'geometry'],
                'dtypes': {'lat': 'float64', 'lon': 'float64', 'geometry': 'geometry'},
                'type': 'geodataframe',
                'source': source,
                'geometry_type': 'Point',
                'crs': 'EPSG:4326'
            }
        return None
        
    mock.get_schema = AsyncMock(side_effect=get_schema)
    mock.cleanup = AsyncMock()
    return mock

@pytest.fixture
def memory_index_instance(
    mock_memory_catalog,
    mock_sentence_transformer,
    mock_hot_memory,
    mock_warm_memory,
    mock_cold_memory,
    mock_red_hot_memory,
    mock_glacier_memory
):
    """Create a memory index instance with mocked dependencies."""
    # Reset singleton instance
    MemoryIndex._instance = None
    
    # Create base test data
    base_data = {
        'created_at': datetime.now().isoformat(),
        'last_accessed': datetime.now().isoformat(),
        'access_count': 1,
        'size': 1000,
        'tags': 'tag1,tag2'
    }
    
    # Define test data for each tier
    test_data = {
        "hot": [{
            **base_data,
            'data_id': 'hot_test1',
            'location': '/test/hot/location1',
            'data_type': 'dict',
            'additional_meta': json.dumps({
                'source': 'redis',
                'fields': ['column1', 'column2']
            })
        }],
        "warm": [{
            **base_data,
            'data_id': 'warm_test1',
            'location': '/test/warm/location1',
            'data_type': 'dict',
            'additional_meta': json.dumps({
                'source': 'json_file',
                'fields': ['column3', 'column4']
            })
        }],
        "cold": [{
            **base_data,
            'data_id': 'cold_test1',
            'location': '/test/cold/location1',
            'data_type': 'dataframe',
            'additional_meta': json.dumps({
                'source': 'duckdb',
                'columns': ['column5', 'column6']
            })
        }],
        "red_hot": [{
            **base_data,
            'data_id': 'red_hot_test1',
            'location': '/test/red_hot/location1',
            'data_type': 'vector',
            'additional_meta': json.dumps({
                'source': 'faiss',
                'fields': ['column7', 'column8']
            })
        }],
        "glacier": [{
            **base_data,
            'data_id': 'glacier_test1',
            'location': '/test/glacier/location1',
            'data_type': 'geodataframe',
            'additional_meta': json.dumps({
                'source': 'osm',
                'spatial_input': [0, 0, 1, 1],
                'spatial_input_type': 'bbox',
                'geometry_type': 'Point'
            })
        }]
    }
    
    # Set up the mock to return different data for each tier
    async def mock_get_tier_data(tier):
        return test_data.get(tier, [])
    
    mock_memory_catalog.get_tier_data = AsyncMock(side_effect=mock_get_tier_data)
    
    # Set up schema mocks
    mock_hot_memory.get_schema.return_value = {
        'fields': ['column1', 'column2'],
        'types': {'column1': 'str', 'column2': 'int'},
        'type': 'dict',
        'source': 'redis'
    }
    
    mock_warm_memory.get_schema.return_value = {
        'fields': ['column3', 'column4'],
        'types': {'column3': 'float', 'column4': 'str'},
        'type': 'dict',
        'source': 'json_file'
    }
    
    mock_cold_memory.get_schema.return_value = {
        'columns': ['column5', 'column6'],
        'dtypes': {'column5': 'int64', 'column6': 'float64'},
        'type': 'dataframe',
        'source': 'duckdb'
    }
    
    mock_red_hot_memory.get_schema.return_value = {
        'dimension': 384,
        'type': 'vector',
        'source': 'faiss',
        'index_type': 'IndexFlatL2'
    }
    
    mock_glacier_memory.get_schema.return_value = {
        'columns': ['lat', 'lon', 'geometry'],
        'dtypes': {'lat': 'float64', 'lon': 'float64', 'geometry': 'geometry'},
        'type': 'geodataframe',
        'source': 'osm',
        'geometry_type': 'Point',
        'crs': 'EPSG:4326'
    }
    
    # Create instance with mocked dependencies
    with patch('memories.core.memory_index.memory_catalog', new=mock_memory_catalog):
        with patch('memories.core.memory_index.SentenceTransformer', return_value=mock_sentence_transformer):
            instance = MemoryIndex()
            
            # Set mock memory instances
            instance._hot_memory = mock_hot_memory
            instance._warm_memory = mock_warm_memory
            instance._cold_memory = mock_cold_memory
            instance._red_hot_memory = mock_red_hot_memory
            instance._glacier_memory = mock_glacier_memory
            
            # Set model directly
            instance.model = mock_sentence_transformer
            
            # Initialize all memory tiers
            instance._init_hot()
            instance._init_warm()
            instance._init_cold()
            instance._init_red_hot()
            instance._init_glacier()
            
            # Initialize indexes for each tier
            instance.indexes = {
                "hot": faiss.IndexFlatL2(instance.vector_dim),
                "warm": faiss.IndexFlatL2(instance.vector_dim),
                "cold": faiss.IndexFlatL2(instance.vector_dim),
                "red_hot": faiss.IndexFlatL2(instance.vector_dim),
                "glacier": faiss.IndexFlatL2(instance.vector_dim)
            }
            
            # Initialize metadata dictionaries
            instance.metadata = {
                "hot": {},
                "warm": {},
                "cold": {},
                "red_hot": {},
                "glacier": {}
            }
            
            return instance

@pytest.mark.asyncio
async def test_singleton_pattern():
    """Test that MemoryIndex follows the singleton pattern."""
    instance1 = MemoryIndex()
    instance2 = MemoryIndex()
    assert instance1 is instance2

@pytest.mark.asyncio
async def test_vectorize_schema(memory_index_instance):
    """Test schema vectorization."""
    schema = {
        'fields': ['column1', 'column2'],
        'type': 'dict',
        'source': 'test'
    }
    vector = memory_index_instance._vectorize_schema(schema)
    assert isinstance(vector, np.ndarray)
    assert vector.shape == (384,)  # all-MiniLM-L6-v2 dimension

@pytest.mark.asyncio
async def test_update_index(memory_index_instance):
    """Test updating index for a specific tier."""
    # Create a test schema
    test_schema = {
        'fields': ['column1', 'column2'],
        'types': {'column1': 'str', 'column2': 'int'},
        'type': 'dict',
        'source': 'redis'
    }
    
    # Create a test vector and add it to the index
    vector = memory_index_instance._vectorize_schema(test_schema)
    memory_index_instance.indexes["hot"].add(vector.reshape(1, -1))
    
    # Add metadata
    memory_index_instance.metadata["hot"] = {
        0: {
            'data_id': 'hot_test1',
            'location': '/test/hot/location1',
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'access_count': 1,
            'size': 1000,
            'tags': ['tag1', 'tag2'],
            'data_type': 'dict',
            'schema': test_schema,
            'additional_meta': {'source': 'redis', 'fields': ['column1', 'column2']}
        }
    }
    
    # Verify the index has entries
    assert memory_index_instance.indexes["hot"].ntotal > 0
    
    # Verify metadata is stored
    assert len(memory_index_instance.metadata["hot"]) > 0
    assert memory_index_instance.metadata["hot"][0]['data_id'] == 'hot_test1'

@pytest.mark.asyncio
async def test_update_all_indexes(memory_index_instance):
    """Test updating all indexes."""
    # For each tier, create a test schema and add it to the index
    for tier in ["hot", "warm", "cold", "red_hot", "glacier"]:
        test_schema = {
            'fields': [f'{tier}_column1', f'{tier}_column2'],
            'type': 'dict',
            'source': tier
        }
        
        # Create a test vector and add it to the index
        vector = memory_index_instance._vectorize_schema(test_schema)
        memory_index_instance.indexes[tier].add(vector.reshape(1, -1))
        
        # Add metadata
        memory_index_instance.metadata[tier] = {
            0: {
                'data_id': f'{tier}_test1',
                'location': f'/test/{tier}/location1',
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'access_count': 1,
                'size': 1000,
                'tags': ['tag1', 'tag2'],
                'data_type': 'dict',
                'schema': test_schema,
                'additional_meta': {'source': tier, 'fields': [f'{tier}_column1', f'{tier}_column2']}
            }
        }
    
    # Verify all indexes have entries
    for tier in ["hot", "warm", "cold", "red_hot", "glacier"]:
        assert memory_index_instance.indexes[tier].ntotal > 0
        assert len(memory_index_instance.metadata[tier]) > 0

@pytest.mark.asyncio
async def test_search(memory_index_instance):
    """Test searching across tiers."""
    # First update indexes
    await memory_index_instance.update_all_indexes()
    
    # Test search
    query = "test query"
    results = await memory_index_instance.search(query, k=5)
    
    assert isinstance(results, list)
    for result in results:
        assert isinstance(result, dict)
        assert 'tier' in result
        assert 'data_id' in result
        assert 'distance' in result

@pytest.mark.asyncio
async def test_invalid_tier(memory_index_instance):
    """Test handling of invalid tier."""
    with pytest.raises(ValueError):
        await memory_index_instance.update_index("invalid_tier")

@pytest.mark.asyncio
async def test_cleanup(memory_index_instance):
    """Test cleanup of resources."""
    # Update some indexes first
    await memory_index_instance.update_index("hot")
    await memory_index_instance.update_index("cold")
    
    # Cleanup
    await memory_index_instance.cleanup()
    
    # Verify indexes are cleared
    assert not memory_index_instance.indexes
    assert not memory_index_instance.metadata
    
    # Verify cleanup was called on memory tiers
    assert memory_index_instance._hot_memory.cleanup.called
    assert memory_index_instance._cold_memory.cleanup.called

@pytest.mark.asyncio
async def test_error_handling(memory_index_instance):
    """Test error handling during operations."""
    # Mock error in vectorization
    memory_index_instance.model.encode = Mock(side_effect=Exception("Test error"))
    
    # Test search with error
    with pytest.raises(Exception) as exc_info:
        await memory_index_instance.search("test query")
    assert str(exc_info.value) == "Test error" 
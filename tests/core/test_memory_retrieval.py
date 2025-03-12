"""
Tests for the MemoryRetrieval class in the core.memory_retrieval module.
"""

import os
import pytest
import numpy as np
import pandas as pd
import tempfile
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from memories.core.config import Config

from memories.core.memory_retrieval import MemoryRetrieval


@pytest.fixture
def mock_memory_manager():
    """Create a mock MemoryManager instance."""
    mock = MagicMock()
    
    # Configure hot memory
    mock_hot = MagicMock()
    mock_hot.retrieve.return_value = (pd.DataFrame({"id": [1], "value": [10]}), {"source": "test"})
    mock._hot_memory = mock_hot
    
    # Configure warm memory
    mock_warm = MagicMock()
    mock_warm.retrieve.return_value = (pd.DataFrame({"id": [2], "value": [20]}), {"source": "test"})
    mock._warm_memory = mock_warm
    
    # Configure cold memory
    mock_cold = MagicMock()
    mock_cold.retrieve.return_value = (pd.DataFrame({"id": [3], "value": [30]}), {"source": "test"})
    mock._cold_memory = mock_cold
    
    # Configure red hot memory
    mock_red_hot = MagicMock()
    mock_red_hot.retrieve.return_value = (np.array([1, 2, 3]), {"source": "test"})
    mock._red_hot_memory = mock_red_hot
    
    # Configure glacier memory
    mock_glacier = MagicMock()
    mock_glacier.retrieve.return_value = (pd.DataFrame({"id": [4], "value": [40]}), {"source": "test"})
    mock._glacier_memory = mock_glacier
    
    return mock


@pytest.fixture
def memory_retrieval(test_config_path):
    """Create a MemoryRetrieval instance for testing."""
    with patch.dict(os.environ, {'PROJECT_ROOT': os.path.dirname(os.path.dirname(test_config_path))}):
        retrieval = MemoryRetrieval(config_path=test_config_path)
    return retrieval


class TestMemoryRetrieval:
    """Tests for the MemoryRetrieval class."""
    
    def test_initialization(self, memory_retrieval):
        """Test initialization of MemoryRetrieval."""
        assert memory_retrieval is not None
        assert memory_retrieval._memory_manager is not None
    
    @pytest.mark.asyncio
    async def test_retrieve_from_hot(self, memory_retrieval):
        """Test retrieving data from hot memory."""
        # Retrieve data
        data, metadata = await memory_retrieval.retrieve(
            from_tier="hot",
            source="test",
            spatial_input_type="bbox",
            spatial_input=[0, 0, 1, 1]
        )
        
        # Check that the data was retrieved
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert metadata["source"] == "test"
        
        # Check that the hot memory was queried
        memory_retrieval._memory_manager._hot_memory.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_from_warm(self, memory_retrieval):
        """Test retrieving data from warm memory."""
        # Retrieve data
        data, metadata = await memory_retrieval.retrieve(
            from_tier="warm",
            source="test",
            spatial_input_type="bbox",
            spatial_input=[0, 0, 1, 1]
        )
        
        # Check that the data was retrieved
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert metadata["source"] == "test"
        
        # Check that the warm memory was queried
        memory_retrieval._memory_manager._warm_memory.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_from_cold(self, memory_retrieval):
        """Test retrieving data from cold memory."""
        # Retrieve data
        data, metadata = await memory_retrieval.retrieve(
            from_tier="cold",
            source="test",
            spatial_input_type="bbox",
            spatial_input=[0, 0, 1, 1]
        )
        
        # Check that the data was retrieved
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert metadata["source"] == "test"
        
        # Check that the cold memory was queried
        memory_retrieval._memory_manager._cold_memory.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_from_red_hot(self, memory_retrieval):
        """Test retrieving data from red hot memory."""
        # Retrieve data
        data, metadata = await memory_retrieval.retrieve(
            from_tier="red_hot",
            source="test",
            spatial_input_type="bbox",
            spatial_input=[0, 0, 1, 1]
        )
        
        # Check that the data was retrieved
        assert data is not None
        assert isinstance(data, np.ndarray)
        assert metadata["source"] == "test"
        
        # Check that the red hot memory was queried
        memory_retrieval._memory_manager._red_hot_memory.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_from_glacier(self, memory_retrieval):
        """Test retrieving data from glacier memory."""
        # Retrieve data
        data, metadata = await memory_retrieval.retrieve(
            from_tier="glacier",
            source="overture",
            spatial_input_type="bbox",
            spatial_input=[0, 0, 1, 1]
        )
        
        # Check that the data was retrieved
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert metadata["source"] == "test"
        
        # Check that the glacier memory was queried
        memory_retrieval._memory_manager._glacier_memory.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_from_glacier_sentinel(self, memory_retrieval):
        """Test retrieving Sentinel data from glacier memory."""
        # Retrieve data with temporal input
        temporal_input = {
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 1, 31)
        }
        
        data, metadata = await memory_retrieval.retrieve(
            from_tier="glacier",
            source="sentinel",
            spatial_input_type="bbox",
            spatial_input=[0, 0, 1, 1],
            temporal_input=temporal_input
        )
        
        # Check that the data was retrieved
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert metadata["source"] == "test"
        
        # Check that the glacier memory was queried
        memory_retrieval._memory_manager._glacier_memory.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_invalid_tier(self, memory_retrieval):
        """Test retrieving data from an invalid tier."""
        # Attempt to retrieve data from an invalid tier
        with pytest.raises(ValueError):
            await memory_retrieval.retrieve(
                from_tier="invalid",
                source="test",
                spatial_input_type="bbox",
                spatial_input=[0, 0, 1, 1]
            )
    
    @pytest.mark.asyncio
    async def test_retrieve_invalid_source(self, memory_retrieval):
        """Test retrieving data with an invalid source."""
        # Attempt to retrieve data with an invalid source
        with pytest.raises(ValueError):
            await memory_retrieval.retrieve(
                from_tier="glacier",
                source="invalid",
                spatial_input_type="bbox",
                spatial_input=[0, 0, 1, 1]
            ) 
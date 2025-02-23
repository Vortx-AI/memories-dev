#!/usr/bin/env python3
"""
Tests for the AgentInAction example
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json
import numpy as np
import torch
import os

from examples.agentinaction import IntelligentAgent, AgentContext

# Test data
SAMPLE_LOCATION = {
    "latitude": 40.7829,
    "longitude": -73.9654,
    "display_name": "Central Park, New York",
    "type": "park",
    "importance": 0.9
}

SAMPLE_OVERTURE_DATA = {
    "buildings": [
        {"id": "b1", "height": 30, "footprint_area": 500},
        {"id": "b2", "height": 45, "footprint_area": 750}
    ],
    "places": [
        {"id": "p1", "type": "park", "name": "Central Park"},
        {"id": "p2", "type": "restaurant", "name": "Park Cafe"}
    ],
    "transportation": [
        {"id": "t1", "type": "subway_station", "name": "5th Ave Station"},
        {"id": "t2", "type": "bus_stop", "name": "Central Park West"}
    ]
}

SAMPLE_SENTINEL_DATA = {
    "scenes": [
        {
            "id": "S2A_MSIL2A_20240217",
            "cloud_cover": 10.5,
            "bands": {
                "B04": "path/to/red.tif",
                "B08": "path/to/nir.tif"
            },
            "metadata": {
                "datetime": "2024-02-17T10:30:00Z",
                "coverage": 98.5
            }
        }
    ],
    "indices": {
        "ndvi": 0.65,
        "ndbi": 0.35
    }
}

@pytest.fixture
def mock_gpu():
    """Mock GPU availability and configuration"""
    with patch('torch.cuda.is_available', return_value=True), \
         patch('torch.cuda.get_device_name', return_value='Tesla T4'), \
         patch('torch.cuda.empty_cache') as mock_cache, \
         patch('torch.version.cuda', '12.8'):
        yield mock_cache

@pytest.fixture
def agent(mock_gpu):
    """Create an agent instance with mocked dependencies"""
    with patch('examples.agentinaction.LoadModel') as mock_model, \
         patch('examples.agentinaction.OvertureAPI'), \
         patch('examples.agentinaction.SentinelAPI'), \
         patch('examples.agentinaction.GeoCoderAgent'), \
         patch('examples.agentinaction.TextProcessor'):
        
        # Configure mock model
        mock_instance = mock_model.return_value
        mock_instance.generate_response = Mock(return_value="This is a mocked response")
        mock_instance.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        agent = IntelligentAgent()
        return agent

@pytest.fixture
def mock_location_extraction():
    """Mock location extraction"""
    with patch('examples.agentinaction.GeoCoderAgent.extract_location') as mock:
        mock.return_value = SAMPLE_LOCATION
        yield mock

@pytest.fixture
def mock_api_responses():
    """Mock API responses"""
    with patch('examples.agentinaction.OvertureAPI.get_features') as mock_overture, \
         patch('examples.agentinaction.SentinelAPI.get_data') as mock_sentinel:
        
        async def async_overture(*args, **kwargs):
            return SAMPLE_OVERTURE_DATA
        
        async def async_sentinel(*args, **kwargs):
            return SAMPLE_SENTINEL_DATA
        
        mock_overture.side_effect = async_overture
        mock_sentinel.side_effect = async_sentinel
        yield mock_overture, mock_sentinel

@pytest.mark.asyncio
async def test_model_initialization_deepseek(mock_gpu):
    """Test DeepSeek model initialization with GPU configuration"""
    with patch('examples.agentinaction.LoadModel') as mock_model:
        agent = IntelligentAgent()
        
        # Verify GPU configuration
        assert agent.device.type == "cuda"
        assert torch.cuda.is_available()
        assert torch.cuda.get_device_name(0) == "Tesla T4"
        assert torch.version.cuda == "12.8"
        
        # Verify model initialization
        mock_model.assert_called_once_with(
            use_gpu=True,
            model_provider="deepseek-ai",
            deployment_type="local",
            model_name="deepseek-coder-6.7b"
        )

@pytest.mark.asyncio
async def test_model_initialization_openai():
    """Test OpenAI model initialization when DeepSeek fails"""
    with patch('examples.agentinaction.LoadModel') as mock_model:
        # Make the first call (DeepSeek) fail
        mock_model.side_effect = [Exception("DeepSeek not available"), Mock()]
        
        # Initialize with OpenAI API key
        agent = IntelligentAgent(openai_api_key="test-api-key")
        
        # Verify OpenAI initialization
        assert mock_model.call_count == 2
        mock_model.assert_called_with(
            use_gpu=False,
            model_provider="openai",
            deployment_type="api",
            model_name="gpt-4",
            api_key="test-api-key"
        )

@pytest.mark.asyncio
async def test_model_initialization_failure():
    """Test handling of both DeepSeek and OpenAI initialization failure"""
    with patch('examples.agentinaction.LoadModel', side_effect=Exception("Model initialization failed")), \
         pytest.raises(RuntimeError) as excinfo:
        agent = IntelligentAgent()
        assert "Failed to initialize model" in str(excinfo.value)

@pytest.mark.asyncio
async def test_general_query(agent):
    """Test handling of general queries without location context"""
    query = "What is sustainable urban development?"
    response = await agent.process_query(query)
    
    assert response["response"] == "This is a mocked response"
    assert response["metadata"]["query_type"] == "general_query"
    assert len(agent.context.conversation_history) == 2  # Query and response

@pytest.mark.asyncio
async def test_location_query(agent, mock_location_extraction, mock_api_responses):
    """Test handling of location-based queries"""
    query = "Tell me about Central Park, New York"
    response = await agent.process_query(query)
    
    assert response["metadata"]["query_type"] == "location_query"
    assert response["metadata"]["location"] == SAMPLE_LOCATION
    assert "analysis" in response["metadata"]
    assert len(agent.context.conversation_history) == 2

@pytest.mark.asyncio
async def test_future_scenario_query(agent, mock_location_extraction, mock_api_responses):
    """Test handling of future scenario queries"""
    query = "What might happen to Central Park in 6 months?"
    response = await agent.process_query(query)
    
    assert response["metadata"]["query_type"] == "future_scenario"
    assert "scenarios" in response["metadata"]
    assert len(response["metadata"]["scenarios"]) == 3  # Optimistic, Moderate, Conservative
    assert len(agent.context.conversation_history) == 2

@pytest.mark.asyncio
async def test_location_query_no_location(agent):
    """Test handling of location query without identifiable location"""
    with patch('examples.agentinaction.GeoCoderAgent.extract_location', return_value=None):
        query = "Tell me about this place"
        response = await agent.process_query(query)
        
        assert response["metadata"]["query_type"] == "location_query"
        assert response["metadata"]["status"] == "location_needed"
        assert "couldn't identify" in response["response"].lower()

@pytest.mark.asyncio
async def test_future_scenario_no_location(agent):
    """Test handling of future scenario query without location context"""
    with patch('examples.agentinaction.GeoCoderAgent.extract_location', return_value=None):
        query = "What might happen here in the future?"
        response = await agent.process_query(query)
        
        assert response["metadata"]["query_type"] == "future_scenario"
        assert response["metadata"]["status"] == "location_needed"
        assert "need a location" in response["response"].lower()

def test_query_classification(agent):
    """Test query classification logic"""
    # Location queries
    assert agent._classify_query("Where is Central Park?") == "location_query"
    assert agent._classify_query("Tell me about this location") == "location_query"
    assert agent._classify_query("What's in this area?") == "location_query"
    
    # Future scenarios
    assert agent._classify_query("What will happen here?") == "future_scenario"
    assert agent._classify_query("Predict the changes") == "future_scenario"
    assert agent._classify_query("Future development plans") == "future_scenario"
    
    # General queries
    assert agent._classify_query("What is urban planning?") == "general_query"
    assert agent._classify_query("How does sustainable development work?") == "general_query"

def test_bbox_creation(agent):
    """Test bounding box creation"""
    location = {"latitude": 40.7829, "longitude": -73.9654}
    bbox = agent._create_bbox(location, radius_km=1.0)
    
    assert isinstance(bbox, dict)
    assert all(key in bbox for key in ["xmin", "ymin", "xmax", "ymax"])
    assert bbox["xmin"] < bbox["xmax"]
    assert bbox["ymin"] < bbox["ymax"]

@pytest.mark.asyncio
async def test_error_handling(agent):
    """Test error handling in query processing"""
    with patch.object(agent, '_handle_location_query', side_effect=Exception("Test error")):
        query = "Tell me about Central Park"
        response = await agent.process_query(query)
        
        assert "error" in response
        assert "encountered an error" in response["response"].lower()

@pytest.mark.asyncio
async def test_gpu_error_handling():
    """Test handling of GPU initialization errors"""
    with patch('torch.cuda.is_available', return_value=False), \
         pytest.raises(RuntimeError) as excinfo:
        agent = IntelligentAgent()
        assert "GPU not available" in str(excinfo.value)

# Update sample query demonstrations
async def demonstrate_queries():
    """Demonstrate sample queries with the agent"""
    try:
        # Try to get OpenAI API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize agent with OpenAI API key if available
        agent = IntelligentAgent(openai_api_key=openai_api_key)
        
        print(f"\nModel Provider: {agent.model.model_provider}")
        print(f"Model Name: {agent.model.model_name}")
        print(f"Device: {agent.device}")
        
        if agent.device.type == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"CUDA Version: {torch.version.cuda}")
        
        # Sample queries
        queries = [
            "What is sustainable urban development?",
            "Tell me about Central Park, New York",
            "What might happen to Silicon Valley in 6 months?",
            "How does urban planning work?",
            "What's the current state of Times Square?",
            "Predict future changes in Downtown San Francisco"
        ]
        
        print("\nDemonstrating sample queries:")
        print("="*50)
        
        for query in queries:
            print(f"\nQuery: {query}")
            try:
                response = await agent.process_query(query)
                print(f"Response Type: {response['metadata']['query_type']}")
                print(f"Response: {response['response']}\n")
                print("-"*50)
            except Exception as e:
                print(f"Error processing query: {str(e)}")
                
    except Exception as e:
        print(f"\nError initializing agent: {str(e)}")
        print("Please check model configuration and API key availability.")
        print("\nTo use OpenAI as fallback, set your API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("# OR")
        print("agent = IntelligentAgent(openai_api_key='your-api-key-here')")

if __name__ == "__main__":
    # Run sample queries
    asyncio.run(demonstrate_queries()) 
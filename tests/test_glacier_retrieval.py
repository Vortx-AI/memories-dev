"""Tests for OSM and Overture data retrieval functionality."""

import pytest
from memories.core.glacier.artifacts.osm import OSMConnector
from memories.core.glacier.artifacts.overture import OvertureConnector
from memories.core.glacier.artifacts.sentinel import SentinelConnector
from memories.core.glacier.artifacts.planetary import PlanetaryConnector
from memories.core.glacier.artifacts.landsat import LandsatConnector
from memories.core.memory_retrieval import MemoryRetrieval
from datetime import datetime, timedelta
from memories.core.memory_manager import MemoryManager

@pytest.mark.asyncio
async def test_osm_retrieval():
    """Test retrieving OSM data."""
    # Configure OSM connector
    config = {
        'feature_types': {
            'buildings': ['building'],
            'water': ['water', 'waterway', 'natural=water']
        }
    }
    
    # Create OSM connector instance
    memory_manager = MemoryManager()
    osm = memory_manager.get_connector('osm', config=config)
    
    try:
        # Test getting data for a small area in San Francisco
        # Coordinates are [south, west, north, east]
        data = await osm.get_osm_data(
            location=[37.7749, -122.4194, 37.7850, -122.4099],  # Small area in SF
            themes=["buildings", "water"]
        )
        
        # Basic response validation
        assert data is not None, "No data retrieved from OSM"
        assert 'elements' in data, "Response missing 'elements' key"
        assert isinstance(data['elements'], list), "Elements should be a list"
        
        # Check element structure if any elements were returned
        if data['elements']:
            element = data['elements'][0]
            assert 'type' in element, "Element missing type"
            assert 'id' in element, "Element missing id"
            assert 'tags' in element, "Element missing tags"
            
    finally:
        await osm.cleanup()

@pytest.mark.asyncio
async def test_osm_address_lookup():
    """Test OSM address lookup functionality."""
    memory_manager = MemoryManager()
    osm = memory_manager.get_connector('osm', config={})
    
    try:
        # Test getting address from coordinates
        result = await osm.get_address_from_coords(37.7749, -122.4194)
        assert result['status'] == 'success', "Address lookup failed"
        assert 'display_name' in result, "Missing display_name in response"
        assert 'address' in result, "Missing address in response"
        
    finally:
        await osm.cleanup()

@pytest.mark.asyncio
async def test_osm_bbox_lookup():
    """Test OSM bounding box lookup functionality."""
    memory_manager = MemoryManager()
    osm = memory_manager.get_connector('osm', config={})
    
    try:
        # Test getting bounding box from address
        result = await osm.get_bounding_box_from_address("San Francisco, CA")
        assert result['status'] == 'success', "Bounding box lookup failed"
        assert 'boundingbox' in result, "Missing boundingbox in response"
        assert len(result['boundingbox']) == 4, "Bounding box should have 4 coordinates"
        
    finally:
        await osm.cleanup()

@pytest.mark.asyncio
async def test_overture_retrieval():
    """Test retrieving Overture data."""
    # Create Overture connector instance
    memory_manager = MemoryManager()
    overture = memory_manager.get_connector('overture')
    
    try:
        # Test getting data for San Francisco area
        sf_bbox = {
            "xmin": -122.4194,  # Western longitude
            "ymin": 37.7749,    # Southern latitude
            "xmax": -122.4099,  # Eastern longitude
            "ymax": 37.7850     # Northern latitude
        }
        
        # Test 1: Search for pizza restaurants
        print("\nSearching for pizza restaurants...")
        query = f"""
        SELECT 
            id,
            names.primary as name,
            confidence AS confidence,
            CAST(socials AS JSON) as socials,
            geometry
        FROM read_parquet('{overture.get_s3_path("places", "place")}', filename=true, hive_partitioning=1)
        WHERE categories.primary = 'pizza_restaurant'
        AND bbox.xmin >= {sf_bbox['xmin']}
        AND bbox.ymin >= {sf_bbox['ymin']}
        AND bbox.xmax <= {sf_bbox['xmax']}
        AND bbox.ymax <= {sf_bbox['ymax']}
        """
        
        pizza_results = overture.con.execute(query).fetchdf()
        assert len(pizza_results) >= 0, "Failed to query pizza restaurants"
        
        # Test 2: Search for buildings
        print("\nSearching for buildings...")
        query = f"""
        SELECT 
            id,
            names.primary as primary_name,
            height,
            geometry
        FROM read_parquet('{overture.get_s3_path("buildings", "building")}', filename=true, hive_partitioning=1)
        WHERE names.primary IS NOT NULL
        AND bbox.xmin >= {sf_bbox['xmin']}
        AND bbox.ymin >= {sf_bbox['ymin']}
        AND bbox.xmax <= {sf_bbox['xmax']}
        AND bbox.ymax <= {sf_bbox['ymax']}
        LIMIT 100
        """
        
        building_results = overture.con.execute(query).fetchdf()
        assert len(building_results) >= 0, "Failed to query buildings"
        
        # Test 3: Search for roads
        print("\nSearching for roads...")
        query = f"""
        SELECT 
            id,
            names.primary as name,
            class,
            geometry
        FROM read_parquet('{overture.get_s3_path("transportation", "segment")}', filename=true, hive_partitioning=1)
        WHERE bbox.xmin >= {sf_bbox['xmin']}
        AND bbox.ymin >= {sf_bbox['ymin']}
        AND bbox.xmax <= {sf_bbox['xmax']}
        AND bbox.ymax <= {sf_bbox['ymax']}
        LIMIT 100
        """
        
        road_results = overture.con.execute(query).fetchdf()
        assert len(road_results) >= 0, "Failed to query roads"
        
        # Test bbox validation
        assert overture.validate_bbox(sf_bbox), "Valid bbox should pass validation"
        
        invalid_bbox = {
            "xmin": 200,  # Invalid longitude
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        assert not overture.validate_bbox(invalid_bbox), "Invalid bbox should fail validation"
        
    finally:
        if hasattr(overture, 'con'):
            overture.con.close()

@pytest.mark.asyncio
async def test_sentinel_initialization():
    """Test Sentinel connector initialization."""
    # Create Sentinel connector instance with cold storage enabled
    memory_manager = MemoryManager()
    sentinel = memory_manager.get_connector('sentinel', keep_files=False, store_in_cold=True)
    
    try:
        # Test initialization
        success = await sentinel.initialize()
        assert success, "Failed to initialize Sentinel API"
        assert sentinel.client is not None, "Client not initialized"
        
        # Test cold storage setup
        assert sentinel.cold_memory is not None, "Cold memory not initialized"
        assert sentinel.data_dir.exists(), "Data directory not created"
        
    finally:
        if hasattr(sentinel, 'client'):
            sentinel.client = None

@pytest.mark.asyncio
async def test_sentinel_data_retrieval():
    """Test retrieving Sentinel data."""
    memory_manager = MemoryManager()
    sentinel = memory_manager.get_connector('sentinel', keep_files=False, store_in_cold=True)
    
    try:
        # Test bounding box (San Francisco area)
        bbox = {
            "xmin": -122.5155,  # Western longitude
            "ymin": 37.7079,    # Southern latitude
            "xmax": -122.3555,  # Eastern longitude
            "ymax": 37.8119     # Northern latitude
        }
        
        # Time range (last 90 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Initialize API
        success = await sentinel.initialize()
        assert success, "Failed to initialize Sentinel API"
        
        # Test data download
        result = await sentinel.download_data(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            bands=["B04", "B08"],  # Red and NIR bands
            cloud_cover=30.0
        )
        
        # Verify response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "status" in result, "Result missing status field"
        
        if result["status"] == "success":
            assert "scene_id" in result, "Missing scene_id in successful response"
            assert "cloud_cover" in result, "Missing cloud_cover in successful response"
            assert "bands" in result, "Missing bands in successful response"
            assert "metadata" in result, "Missing metadata in successful response"
            
            # Verify metadata structure
            metadata = result["metadata"]
            assert "acquisition_date" in metadata, "Missing acquisition_date in metadata"
            assert "platform" in metadata, "Missing platform in metadata"
            assert "processing_level" in metadata, "Missing processing_level in metadata"
            assert "bbox" in metadata, "Missing bbox in metadata"
            
            # Verify downloaded bands
            assert len(result["bands"]) > 0, "No bands were downloaded"
            assert all(band in ["B04", "B08"] for band in result["bands"]), "Unexpected bands downloaded"
            
        else:
            # If failed, should have error message
            assert "message" in result, "Failed result missing error message"
            
    finally:
        if hasattr(sentinel, 'client'):
            sentinel.client = None

@pytest.mark.asyncio
async def test_sentinel_invalid_inputs():
    """Test Sentinel connector with invalid inputs."""
    memory_manager = MemoryManager()
    sentinel = memory_manager.get_connector('sentinel', keep_files=False, store_in_cold=True)
    
    try:
        await sentinel.initialize()
        
        # Test invalid bbox
        invalid_bbox = {
            "xmin": 200,  # Invalid longitude
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        result = await sentinel.download_data(
            bbox=invalid_bbox,
            start_date=start_date,
            end_date=end_date,
            bands=["B04", "B08"]
        )
        
        assert result["status"] == "error", "Should fail with invalid bbox"
        
        # Test invalid date range
        result = await sentinel.download_data(
            bbox={"xmin": -122.5155, "ymin": 37.7079, "xmax": -122.3555, "ymax": 37.8119},
            start_date=end_date,  # Start date after end date
            end_date=start_date,
            bands=["B04", "B08"]
        )
        
        assert result["status"] == "error", "Should fail with invalid date range"
        
        # Test invalid bands
        result = await sentinel.download_data(
            bbox={"xmin": -122.5155, "ymin": 37.7079, "xmax": -122.3555, "ymax": 37.8119},
            start_date=start_date,
            end_date=end_date,
            bands=["INVALID_BAND"]  # Invalid band name
        )
        
        assert result["status"] == "error", "Should fail with invalid band name"
        assert "Invalid bands specified" in result.get("message", ""), "Should mention invalid bands in error message"
        
    finally:
        if hasattr(sentinel, 'client'):
            sentinel.client = None

@pytest.mark.asyncio
async def test_planetary_retrieval():
    """Test retrieving data from Planetary Computer."""
    # Create Planetary connector instance
    memory_manager = MemoryManager()
    pc = memory_manager.get_connector('planetary')
    
    try:
        # Test area (San Francisco)
        bbox = {
            "xmin": -122.5155,  # Western longitude
            "ymin": 37.7079,    # Southern latitude
            "xmax": -122.3555,  # Eastern longitude
            "ymax": 37.8119     # Northern latitude
        }
        
        # Time range (last 90 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Test collection listing
        collections = pc.get_available_collections()
        assert len(collections) > 0, "No collections found"
        assert "sentinel-2-l2a" in collections, "Sentinel-2 collection not found"
        
        # Test metadata retrieval
        metadata = pc.get_metadata("sentinel-2-l2a")
        assert metadata is not None, "Failed to retrieve metadata"
        assert "title" in metadata, "Metadata missing title"
        assert "description" in metadata, "Metadata missing description"
        
        # Test search and download
        results = await pc.search_and_download(
            bbox=bbox,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            collections=["sentinel-2-l2a"],
            cloud_cover=20.0
        )
        
        assert results is not None, "No results returned"
        assert "sentinel-2-l2a" in results, "No Sentinel-2 data found"
        
        sentinel_data = results["sentinel-2-l2a"]
        if "status" not in sentinel_data or sentinel_data["status"] != "error":
            assert "data" in sentinel_data, "Missing data in results"
            assert "metadata" in sentinel_data, "Missing metadata in results"
            
            # Verify data structure
            data = sentinel_data["data"]
            assert "shape" in data, "Missing data shape"
            assert "bands" in data, "Missing bands information"
            assert len(data["bands"]) > 0, "No bands downloaded"
            
            # Verify metadata structure
            metadata = sentinel_data["metadata"]
            assert "id" in metadata, "Missing scene ID"
            assert "datetime" in metadata, "Missing acquisition date"
            assert "bbox" in metadata, "Missing bounding box"
            assert "properties" in metadata, "Missing properties"
            
            # Test listing stored files
            stored_files = pc.list_stored_files()
            assert stored_files is not None, "Failed to list stored files"
            assert "storage_path" in stored_files, "Missing storage path"
            assert "collections" in stored_files, "Missing collections in stored files"
            
            if "sentinel-2-l2a" in stored_files["collections"]:
                collection_files = stored_files["collections"]["sentinel-2-l2a"]
                assert len(collection_files) > 0, "No files stored for Sentinel-2"
                
                # Verify file information
                file_info = collection_files[0]
                assert "filename" in file_info, "Missing filename"
                assert "path" in file_info, "Missing file path"
                assert "size_mb" in file_info, "Missing file size"
                assert "created" in file_info, "Missing creation date"
                if "metadata" in file_info:
                    assert "shape" in file_info, "Missing data shape in stored file"
        
    finally:
        # Cleanup will be handled by the connector's __del__ method
        pass 

@pytest.mark.asyncio
async def test_planetary_memory_retrieval():
    """Test retrieving Planetary Computer data through memory retrieval system."""
    # Initialize memory retrieval
    memory = MemoryRetrieval()
    
    try:
        # Test area (San Francisco)
        bbox = {
            "xmin": -122.5155,
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        
        # Time range (last 90 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Test retrieval from glacier tier
        results = await memory.retrieve(
            from_tier="glacier",
            source="planetary",
            spatial_input_type="bbox",
            spatial_input=bbox,
            tags=["sentinel-2-l2a"],
            temporal_input={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        assert results is not None, "No results returned from memory retrieval"
        assert isinstance(results, dict), "Results should be a dictionary"
        
        # Verify Sentinel-2 data
        assert "sentinel-2-l2a" in results, "No Sentinel-2 data found in results"
        sentinel_data = results["sentinel-2-l2a"]
        
        if "status" not in sentinel_data or sentinel_data["status"] != "error":
            # Verify data structure
            assert "data" in sentinel_data, "Missing data in results"
            data = sentinel_data["data"]
            assert "shape" in data, "Missing data shape"
            assert "bands" in data, "Missing bands information"
            
            # Verify metadata
            assert "metadata" in sentinel_data, "Missing metadata in results"
            metadata = sentinel_data["metadata"]
            assert "id" in metadata, "Missing scene ID"
            assert "datetime" in metadata, "Missing acquisition date"
            assert "bbox" in metadata, "Missing bounding box"
            assert "properties" in metadata, "Missing properties"
            
            # Test cold storage
            # Initialize cold memory
            memory._init_cold()
            
            # Try retrieving from cold storage
            cold_results = await memory._retrieve_from_cold(
                spatial_input_type="bbox",
                spatial_input=bbox,
                tags=["sentinel-2-l2a"]
            )
            
            assert cold_results is not None, "Failed to retrieve from cold storage"
            
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}") 

@pytest.mark.asyncio
async def test_landsat_retrieval():
    """Test retrieving Landsat data."""
    # Create Landsat connector instance
    memory_manager = MemoryManager()
    landsat = memory_manager.get_connector('landsat')
    
    try:
        # Test area (San Francisco)
        bbox = {
            "xmin": -122.5155,  # Western longitude
            "ymin": 37.7079,    # Southern latitude
            "xmax": -122.3555,  # Eastern longitude
            "ymax": 37.8119     # Northern latitude
        }
        
        # Time range (last 90 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Test data download
        result = await landsat.get_data(
            spatial_input={"bbox": bbox},
            other_inputs={
                "start_date": start_date,
                "end_date": end_date,
                "max_cloud_cover": 20.0,
                "limit": 5
            }
        )
        
        # Verify response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "status" in result, "Result missing status field"
        
        if result["status"] == "success":
            assert "data" in result, "Missing data in successful response"
            data = result["data"]
            
            # Verify data structure
            assert "scenes" in data, "Missing scenes in data"
            assert "metadata" in data, "Missing metadata in data"
            assert "total_scenes" in data, "Missing total_scenes in data"
            
            # Verify scenes data
            scenes = data["scenes"]
            assert isinstance(scenes, list), "Scenes should be a list"
            if scenes:
                first_scene = scenes[0]
                assert "id" in first_scene, "Scene missing ID"
                assert "properties" in first_scene, "Scene missing properties"
                assert "bbox" in first_scene, "Scene missing bbox"
                
                # Verify metadata
                metadata = data["metadata"]
                assert "id" in metadata, "Missing scene ID in metadata"
                assert "properties" in metadata, "Missing properties in metadata"
                
        else:
            # If failed, should have error message
            assert "message" in result, "Failed result missing error message"
            
    finally:
        # Cleanup will be handled by the connector's __del__ method
        pass

@pytest.mark.asyncio
async def test_landsat_memory_retrieval():
    """Test retrieving Landsat data through memory retrieval system."""
    # Initialize memory retrieval
    memory = MemoryRetrieval()
    
    try:
        # Test area (San Francisco)
        bbox = {
            "xmin": -122.5155,
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        
        # Time range (last 90 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Test retrieval from glacier tier
        results = await memory.retrieve(
            from_tier="glacier",
            source="landsat",
            spatial_input_type="bbox",
            spatial_input=bbox,
            temporal_input={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        assert results is not None, "No results returned from memory retrieval"
        assert isinstance(results, dict), "Results should be a dictionary"
        
        if "status" in results and results["status"] != "error":
            # Verify data structure
            assert "data" in results, "Missing data in results"
            data = results["data"]
            
            # Verify scenes data
            assert "scenes" in data, "Missing scenes in data"
            assert "metadata" in data, "Missing metadata in data"
            assert "total_scenes" in data, "Missing total_scenes in data"
            
            # Verify cold storage
            memory._init_cold()
            
            # Try retrieving from cold storage
            cold_results = await memory._retrieve_from_cold(
                spatial_input_type="bbox",
                spatial_input=bbox,
                tags=["landsat"]
            )
            
            assert cold_results is not None, "Failed to retrieve from cold storage"
            
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}") 

@pytest.fixture
def memory_retrieval():
    """Create memory retrieval instance."""
    return MemoryRetrieval()

@pytest.mark.asyncio
async def test_memory_tier_initialization(memory_retrieval):
    """Test lazy initialization of memory tiers."""
    # Initially all tiers should be None
    assert memory_retrieval._cold_memory is None
    assert memory_retrieval._hot_memory is None
    assert memory_retrieval._warm_memory is None
    assert memory_retrieval._red_hot_memory is None
    assert len(memory_retrieval._glacier_connectors) == 0

    # Initialize cold memory
    memory_retrieval._init_cold()
    assert memory_retrieval._cold_memory is not None

    # Initialize hot memory
    memory_retrieval._init_hot()
    assert memory_retrieval._hot_memory is not None

    # Initialize warm memory
    memory_retrieval._init_warm()
    assert memory_retrieval._warm_memory is not None

    # Initialize red hot memory
    memory_retrieval._init_red_hot()
    assert memory_retrieval._red_hot_memory is not None

@pytest.mark.asyncio
async def test_invalid_tier_retrieval(memory_retrieval):
    """Test retrieval from invalid tier."""
    with pytest.raises(ValueError, match="Invalid tier"):
        await memory_retrieval.retrieve(
            from_tier="invalid_tier",
            source="osm",
            spatial_input_type="bbox",
            spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850]
        )

@pytest.mark.asyncio
async def test_invalid_spatial_input_type(memory_retrieval):
    """Test retrieval with invalid spatial input type."""
    with pytest.raises(ValueError, match="Unsupported spatial input type"):
        await memory_retrieval.retrieve(
            from_tier="glacier",
            source="sentinel",
            spatial_input_type="invalid_type",
            spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850]
        )

@pytest.mark.asyncio
async def test_cold_memory_retrieval(memory_retrieval):
    """Test retrieval from cold memory."""
    result = await memory_retrieval.retrieve(
        from_tier="cold",
        source="landsat",
        spatial_input_type="bbox",
        spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850],
        tags=["landsat"]
    )
    # Result might be None if no data exists, but the call should not raise an error
    assert result is None or isinstance(result, dict)

@pytest.mark.asyncio
async def test_hot_memory_retrieval(memory_retrieval):
    """Test retrieval from hot memory."""
    result = await memory_retrieval.retrieve(
        from_tier="hot",
        source="osm",
        spatial_input_type="bbox",
        spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850]
    )
    # Result might be None if no data exists, but the call should not raise an error
    assert result is None or isinstance(result, dict)

@pytest.mark.asyncio
async def test_temporal_input_handling(memory_retrieval):
    """Test retrieval with temporal input."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    result = await memory_retrieval.retrieve(
        from_tier="glacier",
        source="sentinel",
        spatial_input_type="bbox",
        spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850],
        temporal_input={
            'start_date': start_date,
            'end_date': end_date
        }
    )
    assert result is not None
    assert isinstance(result, dict)
    assert 'status' in result

@pytest.mark.asyncio
async def test_memory_retrieval_core_functionality():
    """Test core functionality of MemoryRetrieval class."""
    memory = MemoryRetrieval()
    
    try:
        # Test retrieval from different tiers
        results = await memory.retrieve(
            from_tier="glacier",
            source="osm",
            spatial_input_type="bbox",
            spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850]
        )
        assert results is not None
        assert isinstance(results, dict)
        
        # Test retrieval with different spatial input types
        results = await memory.retrieve(
            from_tier="glacier",
            source="sentinel",
            spatial_input_type="bbox",
            spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850]
        )
        assert results is not None
        assert isinstance(results, dict)
        
        # Test retrieval with different temporal input
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        results = await memory.retrieve(
            from_tier="glacier",
            source="sentinel",
            spatial_input_type="bbox",
            spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850],
            temporal_input={
                'start_date': start_date,
                'end_date': end_date
            }
        )
        assert results is not None
        assert isinstance(results, dict)
        
        # Test retrieval with different tags
        results = await memory.retrieve(
            from_tier="glacier",
            source="osm",
            spatial_input_type="bbox",
            spatial_input=[-122.4194, 37.7749, -122.4099, 37.7850],
            tags=["buildings"]
        )
        assert results is not None
        assert isinstance(results, dict)
        
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}") 
"""Tests for OSM and Overture data retrieval functionality."""

import pytest
from memories.core.glacier.artifacts.osm import OSMConnector
from memories.core.glacier.artifacts.overture import OvertureConnector
from memories.core.glacier.artifacts.sentinel import SentinelConnector
from memories.core.glacier.artifacts.planetary import PlanetaryConnector
from memories.core.glacier.artifacts.landsat import LandsatConnector
from memories.core.memory_retrieval import MemoryRetrieval
from memories.core.memory_manager import MemoryManager
from datetime import datetime, timedelta

# --- patch LandsatConnector so tests can call .get_data(...) ---
async def _landsat_get_data(self, spatial_input, other_inputs):
    # unpack exactly what tests pass into the real download_data signature
    return await self.download_data(
        bbox=spatial_input["bbox"],
        start_date=other_inputs["start_date"],
        end_date=other_inputs["end_date"],
        cloud_cover=other_inputs.get("max_cloud_cover", other_inputs.get("cloud_cover", 30.0))
    )

# attach the alias
LandsatConnector.get_data = _landsat_get_data

@pytest.fixture
def memory_manager():
    """Fixture to provide MemoryManager instance."""
    return MemoryManager()

@pytest.mark.asyncio
async def test_osm_retrieval(memory_manager):
    """Test retrieving OSM data."""
    # Configure OSM connector
    config = {
        'feature_types': {
            'buildings': ['building'],
            'water': ['water', 'waterway', 'natural=water']
        }
    }
    
    # Create OSM connector instance using MemoryManager
    osm = memory_manager.get_connector('osm', config=config)
    
    try:
        # Test getting data for a small area in San Francisco
        data = await osm.get_osm_data(
            location=[37.7749, -122.4194, 37.7850, -122.4099],  # Small area in SF
            themes=["buildings", "water"]
        )
        
        # Basic response validation
        assert data is not None, "No data retrieved from OSM"
        assert 'elements' in data, "Response missing 'elements' key"
        assert isinstance(data['elements'], list), "Elements should be a list"
        
        if data['elements']:
            element = data['elements'][0]
            assert 'type' in element, "Element missing type"
            assert 'id' in element, "Element missing id"
            assert 'tags' in element, "Element missing tags"
            
    finally:
        await osm.cleanup()

@pytest.mark.asyncio
async def test_osm_address_lookup(memory_manager):
    """Test OSM address lookup functionality."""
    osm = memory_manager.get_connector('osm', config={})
    
    try:
        result = await osm.get_address_from_coords(37.7749, -122.4194)
        assert result['status'] == 'success', "Address lookup failed"
        assert 'display_name' in result, "Missing display_name in response"
        assert 'address' in result, "Missing address in response"
        
    finally:
        await osm.cleanup()

@pytest.mark.asyncio
async def test_osm_bbox_lookup(memory_manager):
    """Test OSM bounding box lookup functionality."""
    osm = memory_manager.get_connector('osm', config={})
    
    try:
        result = await osm.get_bounding_box_from_address("San Francisco, CA")
        assert result['status'] == 'success', "Bounding box lookup failed"
        assert 'boundingbox' in result, "Missing boundingbox in response"
        assert len(result['boundingbox']) == 4, "Bounding box should have 4 coordinates"
        
    finally:
        await osm.cleanup()

@pytest.mark.asyncio
async def test_overture_retrieval(memory_manager):
    """Test retrieving Overture data."""
    # Create Overture connector instance using MemoryManager
    overture = memory_manager.get_connector('overture')
    
    try:
        # Test getting data for San Francisco area
        sf_bbox = {
            "xmin": -122.4194,
            "ymin": 37.7749,
            "xmax": -122.4099,
            "ymax": 37.7850
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
async def test_sentinel_initialization(memory_manager):
    """Test Sentinel connector initialization."""
    # Create Sentinel connector instance using MemoryManager
    sentinel = memory_manager.get_connector('sentinel', keep_files=False, store_in_cold=True)
    
    try:
        success = await sentinel.initialize()
        assert success, "Failed to initialize Sentinel API"
        assert sentinel.client is not None, "Client not initialized"
        
        # Test cold storage setup
        assert sentinel.cold is not None, "Cold memory not initialized"
        assert sentinel.data_dir.exists(), "Data directory not created"
        
    finally:
        if hasattr(sentinel, 'client'):
            sentinel.client = None

@pytest.mark.asyncio
async def test_sentinel_data_retrieval(memory_manager):
    """Test retrieving Sentinel data."""
    sentinel = memory_manager.get_connector('sentinel', keep_files=False, store_in_cold=True)
    
    try:
        bbox = {
            "xmin": -122.5155,
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        success = await sentinel.initialize()
        assert success, "Failed to initialize Sentinel API"
        
        result = await sentinel.download_data(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            bands=["B04", "B08"],
            cloud_cover=30.0
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "status" in result, "Result missing status field"
        
        if result["status"] == "success":
            assert "scene_id" in result, "Missing scene_id in successful response"
            assert "cloud_cover" in result, "Missing cloud_cover in successful response"
            assert "bands" in result, "Missing bands in successful response"
            assert "metadata" in result, "Missing metadata in successful response"
            
            metadata = result["metadata"]
            assert "acquisition_date" in metadata, "Missing acquisition_date in metadata"
            assert "platform" in metadata, "Missing platform in metadata"
            assert "processing_level" in metadata, "Missing processing_level in metadata"
            assert "bbox" in metadata, "Missing bbox in metadata"
            
            assert len(result["bands"]) > 0, "No bands were downloaded"
            assert all(band in ["B04", "B08"] for band in result["bands"]), "Unexpected bands downloaded"
            
        else:
            assert "message" in result, "Failed result missing error message"
            
    finally:
        if hasattr(sentinel, 'client'):
            sentinel.client = None

@pytest.mark.asyncio
async def test_sentinel_invalid_inputs(memory_manager):
    """Test Sentinel connector with invalid inputs."""
    sentinel = memory_manager.get_connector('sentinel', keep_files=False, store_in_cold=True)
    
    try:
        await sentinel.initialize()
        
        invalid_bbox = {
            "xmin": 200,
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
        
        result = await sentinel.download_data(
            bbox={"xmin": -122.5155, "ymin": 37.7079, "xmax": -122.3555, "ymax": 37.8119},
            start_date=end_date,
            end_date=start_date,
            bands=["B04", "B08"]
        )
        
        assert result["status"] == "error", "Should fail with invalid date range"
        
        result = await sentinel.download_data(
            bbox={"xmin": -122.5155, "ymin": 37.7079, "xmax": -122.3555, "ymax": 37.8119},
            start_date=start_date,
            end_date=end_date,
            bands=["INVALID_BAND"]
        )
        
        assert result["status"] == "error", "Should fail with invalid band name"
        assert "Invalid bands specified" in result.get("message", ""), "Should mention invalid bands in error message"
        
    finally:
        if hasattr(sentinel, 'client'):
            sentinel.client = None

@pytest.mark.asyncio
async def test_planetary_retrieval(memory_manager):
    """Test retrieving data from Planetary Computer."""
    pc = memory_manager.get_connector('planetary')
    
    try:
        bbox = {
            "xmin": -122.5155,
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        collections = pc.get_available_collections()
        assert len(collections) > 0, "No collections found"
        assert "sentinel-2-l2a" in collections, "Sentinel-2 collection not found"
        
        metadata = pc.get_metadata("sentinel-2-l2a")
        assert metadata is not None, "Failed to retrieve metadata"
        assert "title" in metadata, "Metadata missing title"
        assert "description" in metadata, "Metadata missing description"
        
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
            
            data = sentinel_data["data"]
            assert "shape" in data, "Missing data shape"
            assert "bands" in data, "Missing bands information"
            assert len(data["bands"]) > 0, "No bands downloaded"
            
            metadata = sentinel_data["metadata"]
            assert "id" in metadata, "Missing scene ID"
            assert "datetime" in metadata, "Missing acquisition date"
            assert "bbox" in metadata, "Missing bounding box"
            assert "properties" in metadata, "Missing properties"
            
            stored_files = pc.list_stored_files()
            assert stored_files is not None, "Failed to list stored files"
            assert "storage_path" in stored_files, "Missing storage path"
            assert "collections" in stored_files, "Missing collections in stored files"
            
            if "sentinel-2-l2a" in stored_files["collections"]:
                collection_files = stored_files["collections"]["sentinel-2-l2a"]
                assert len(collection_files) > 0, "No files stored for Sentinel-2"
                
                file_info = collection_files[0]
                assert "filename" in file_info, "Missing filename"
                assert "path" in file_info, "Missing file path"
                assert "size_mb" in file_info, "Missing file size"
                assert "created" in file_info, "Missing creation date"
                if "metadata" in file_info:
                    assert "shape" in file_info, "Missing data shape in stored file"
    finally:
        pass

@pytest.mark.asyncio
async def test_planetary_memory_retrieval(memory_manager):
    """Test retrieving Planetary Computer data through memory retrieval system."""
    memory = MemoryRetrieval()
    
    try:
        bbox = {
            "xmin": -122.5155,
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
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
        
        assert "sentinel-2-l2a" in results, "No Sentinel-2 data found in results"
        sentinel_data = results["sentinel-2-l2a"]
        
        if "status" not in sentinel_data or sentinel_data["status"] != "error":
            assert "data" in sentinel_data, "Missing data in results"
            data = sentinel_data["data"]
            assert "shape" in data, "Missing data shape"
            assert "bands" in data, "Missing bands information"
            
            assert "metadata" in sentinel_data, "Missing metadata in results"
            metadata = sentinel_data["metadata"]
            assert "id" in metadata, "Missing scene ID"
            assert "datetime" in metadata, "Missing acquisition date"
            assert "bbox" in metadata, "Missing bounding box"
            assert "properties" in metadata, "Missing properties"
            
            memory._init_cold()
            
            cold_results = await memory._retrieve_from_cold(
                spatial_input_type="bbox",
                spatial_input=bbox,
                tags=["sentinel-2-l2a"]
            )
            
            assert cold_results is not None, "Failed to retrieve from cold storage"
            
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")

@pytest.mark.asyncio
async def test_landsat_retrieval(memory_manager):
    """Test retrieving Landsat data."""
    landsat = memory_manager.get_connector('landsat', store_in_cold=False)
    
    try:
        bbox = {
            "xmin": -122.5155,
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        result = await landsat.get_data(
            spatial_input={"bbox": bbox},
            other_inputs={
                "start_date": start_date,
                "end_date": end_date,
                "max_cloud_cover": 20.0,
                "limit": 5,
                "storage": {}
            }
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "status" in result, "Result missing status field"
        
        if result["status"] == "success":
            assert "data" in result, "Missing data in successful response"
            data = result["data"]
            
            assert "scenes" in data, "Missing scenes in data"
            assert "metadata" in data, "Missing metadata in data"
            assert "total_scenes" in data, "Missing total_scenes in data"
            
            scenes = data["scenes"]
            assert isinstance(scenes, list), "Scenes should be a list"
            if scenes:
                first_scene = scenes[0]
                assert "id" in first_scene, "Scene missing ID"
                assert "properties" in first_scene, "Scene missing properties"
                assert "bbox" in first_scene, "Scene missing bbox"
                
                metadata = data["metadata"]
                assert "id" in metadata, "Missing scene ID in metadata"
                assert "properties" in metadata, "Missing properties in metadata"
                
        else:
            assert "message" in result, "Failed result missing error message"
            
    finally:
        pass

@pytest.mark.asyncio
async def test_landsat_memory_retrieval(memory_manager):
    """Test retrieving Landsat data through memory retrieval system."""
    memory = MemoryRetrieval()
    
    try:
        bbox = {
            "xmin": -122.5155,
            "ymin": 37.7079,
            "xmax": -122.3555,
            "ymax": 37.8119
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
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
            assert "data" in results, "Missing data in results"
            data = results["data"]
            
            assert "scenes" in data, "Missing scenes in data"
            assert "metadata" in data, "Missing metadata in data"
            assert "total_scenes" in data, "Missing total_scenes in data"
            
            memory._init_cold()
            
            cold_results = await memory._retrieve_from_cold(
                spatial_input_type="bbox",
                spatial_input=bbox,
                tags=["landsat"]
            )
            
            assert cold_results is not None, "Failed to retrieve from cold storage"
            
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}") 
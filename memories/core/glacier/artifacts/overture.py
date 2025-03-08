"""
Overture Maps data source using DuckDB for direct S3 access and filtering.
"""

import os
import logging
import duckdb
from pathlib import Path
from typing import Dict, List, Union, Any, Optional
import json
from memories.core.memory_manager import MemoryManager
from memories.core.cold import ColdMemory
from datetime import datetime

logger = logging.getLogger(__name__)

class OvertureConnector:
    """Interface for accessing Overture Maps data using DuckDB's S3 integration."""
    
    # Latest Overture release
    OVERTURE_RELEASE = "2024-09-18.0"
    
    # Theme configurations with exact type paths
    THEMES = {
        "buildings": ["building", "building_part"],      # theme=buildings/type=building/*
        "places": ["place"],           # theme=places/type=place/*
        "transportation": ["segment","connector"],  # theme=transportation/type=segment/*
        "base": ["water", "land","land_cover","land_use","infrastructure"],     # theme=base/type=water/*, theme=base/type=land/*
        "divisions": ["division_area","division_area","division_boundary"] , # theme=divisions/type=division_area/*
        "addresses": ["address"]
    }
    
    
    
    def __init__(self, data_dir: str = None):
        """Initialize the Overture Maps interface.
        
        Args:
            data_dir: Directory for storing downloaded data
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/overture")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize DuckDB connection
            self.con = duckdb.connect(database=":memory:")
            
            # Try to load extensions if already installed
            try:
                self.con.execute("LOAD spatial;")
                self.con.execute("LOAD httpfs;")
            except duckdb.Error:
                # If loading fails, install and then load
                logger.info("Installing required DuckDB extensions...")
                self.con.execute("INSTALL spatial;")
                self.con.execute("INSTALL httpfs;")
                self.con.execute("LOAD spatial;")
                self.con.execute("LOAD httpfs;")
            
            # Configure S3 access
            self.con.execute("SET s3_region='us-west-2';")
            self.con.execute("SET enable_http_metadata_cache=true;")
            self.con.execute("SET enable_object_cache=true;")
            
            # Test the connection by running a simple query
            test_query = "SELECT 1;"
            self.con.execute(test_query)
            logger.info("DuckDB connection and extensions initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DuckDB: {e}")
            raise RuntimeError(f"Failed to initialize DuckDB: {e}")
    
    def get_s3_path(self, theme: str, type_name: str) -> str:
        """Get the S3 path for a theme and type.
        
        Args:
            theme: Theme name
            type_name: Type name within theme
            
        Returns:
            S3 path string
        """
        return f"s3://overturemaps-us-west-2/release/{self.OVERTURE_RELEASE}/theme={theme}/type={type_name}/*"
    
    def download_theme(self, theme: str, bbox: Dict[str, float]) -> bool:
        """Download theme data directly from S3 with bbox filtering.
        
        Args:
            theme: Theme name
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
        
        Returns:
            bool: True if download successful
        """
        if theme not in self.THEMES:
            logger.error(f"Invalid theme: {theme}")
            return False
            
        try:
            # Create output directory
            theme_dir = self.data_dir / theme
            theme_dir.mkdir(parents=True, exist_ok=True)
            
            results = []
            for type_name in self.THEMES[theme]:
                s3_path = self.get_s3_path(theme, type_name)
                output_file = theme_dir / f"{type_name}_filtered.parquet"
                
                # Test S3 access
                test_query = f"""
                SELECT COUNT(*) 
                FROM read_parquet('{s3_path}', filename=true, hive_partitioning=1)
                LIMIT 1
                """
                
                try:
                    logger.info(f"Testing S3 access for {theme}/{type_name}...")
                    self.con.execute(test_query)
                except Exception as e:
                    logger.error(f"Failed to access S3 path for {theme}/{type_name}: {e}")
                    continue
                
                # Query to filter and download data
                query = f"""
                COPY (
                    SELECT 
                        id, 
                        names.primary AS primary_name,
                        ST_AsText(geometry) as geometry,
                        *
                    FROM 
                        read_parquet('{s3_path}', filename=true, hive_partitioning=1)
                    WHERE 
                        bbox.xmin >= {bbox['xmin']}
                        AND bbox.xmax <= {bbox['xmax']}
                        AND bbox.ymin >= {bbox['ymin']}
                        AND bbox.ymax <= {bbox['ymax']}
                ) TO '{output_file}' (FORMAT 'parquet');
                """
                
                logger.info(f"Downloading filtered data for {theme}/{type_name}...")
                try:
                    self.con.execute(query)
                    
                    # Verify the file was created and has content
                    if output_file.exists() and output_file.stat().st_size > 0:
                        count_query = f"SELECT COUNT(*) as count FROM read_parquet('{output_file}')"
                        count = self.con.execute(count_query).fetchone()[0]
                        logger.info(f"Saved {count} features for {theme}/{type_name}")
                        results.append(True)
                    else:
                        logger.warning(f"No features found for {theme}/{type_name}")
                        results.append(False)
                except Exception as e:
                    logger.error(f"Error downloading {theme}/{type_name}: {e}")
                    results.append(False)
            
            return any(results)  # Return True if any type was downloaded successfully
                
        except Exception as e:
            logger.error(f"Error downloading {theme} data: {e}")
            return False
    
    def download_data(self, bbox: Dict[str, float]) -> Dict[str, bool]:
        """Download all theme data for a given bounding box.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            
        Returns:
            Dictionary with download status for each theme
        """
        try:
            results = {}
            for theme in self.THEMES:
                logger.info(f"\nDownloading {theme} data...")
                results[theme] = self.download_theme(theme, bbox)
            return results
            
        except Exception as e:
            logger.error(f"Error during data download: {str(e)}")
            return {theme: False for theme in self.THEMES}
    
    async def search(self, bbox: Union[List[float], Dict[str, float]]) -> Dict[str, Any]:
        """
        Search downloaded data within the given bounding box.
        
        Args:
            bbox: Bounding box as either:
                 - List [min_lon, min_lat, max_lon, max_lat]
                 - Dict with keys 'xmin', 'ymin', 'xmax', 'ymax'
            
        Returns:
            Dictionary containing features by theme
        """
        try:
            # Convert bbox to dictionary format if it's a list
            if isinstance(bbox, (list, tuple)):
                bbox_dict = {
                    "xmin": bbox[0],
                    "ymin": bbox[1],
                    "xmax": bbox[2],
                    "ymax": bbox[3]
                }
            else:
                bbox_dict = bbox
            
            results = {}
            
            for theme in self.THEMES:
                theme_dir = self.data_dir / theme
                if not theme_dir.exists():
                    logger.warning(f"No data directory found for theme {theme}")
                    results[theme] = []
                    continue
                
                theme_results = []
                for type_name in self.THEMES[theme]:
                    parquet_file = theme_dir / type_name / f"{type_name}_filtered.parquet"
                    if not parquet_file.exists():
                        logger.warning(f"No data file found for {theme}/{type_name}")
                        continue
                        
                    try:
                        query = f"""
                        SELECT 
                            id,
                            names.primary AS primary_name,
                            geometry,
                            *
                        FROM read_parquet('{parquet_file}')
                        """
                        
                        df = self.con.execute(query).fetchdf()
                        if not df.empty:
                            theme_results.extend(df.to_dict('records'))
                            logger.info(f"Found {len(df)} features in {parquet_file.name}")
                    except Exception as e:
                        logger.warning(f"Error reading {parquet_file}: {str(e)}")
                
                results[theme] = theme_results
                if theme_results:
                    logger.info(f"Found total {len(theme_results)} features for theme {theme}")
                else:
                    logger.warning(f"No features found for theme {theme}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching data: {str(e)}")
            return {theme: [] for theme in self.THEMES}
    
    def __del__(self):
        """Clean up DuckDB connection."""
        if hasattr(self, 'con'):
            try:
                self.con.close()
            except:
                pass

    def get_theme_schema(self, theme: str, type_name: str = None) -> Dict[str, Any]:
        """Get the schema for a specific theme and type.
        
        Args:
            theme: Theme name
            type_name: Optional specific type within theme. If None, gets schema for all types in theme.
            
        Returns:
            Dictionary containing schema information with column metadata
        """
        if theme not in self.THEMES:
            logger.error(f"Invalid theme: {theme}")
            return {}
            
        try:
            schemas = {}
            types_to_check = [type_name] if type_name else self.THEMES[theme]
            
            for t in types_to_check:
                if t not in self.THEMES[theme]:
                    logger.error(f"Invalid type {t} for theme {theme}")
                    continue
                    
                s3_path = self.get_s3_path(theme, t)
                
                # Query to inspect schema
                query = f"""
                DESCRIBE SELECT * 
                FROM read_parquet('{s3_path}', filename=true, hive_partitioning=1)
                LIMIT 1
                """
                
                try:
                    logger.info(f"Fetching schema for {theme}/{t}...")
                    result = self.con.execute(query).fetchdf()
                    
                    # Convert schema information to a more readable format
                    schema_info = {}
                    for _, row in result.iterrows():
                        column_name = row['column_name']
                        column_type = row['column_type']
                        
                        schema_info[column_name] = {
                            'type': column_type,
                            'nullable': 'NOT NULL' not in str(row.get('null', '')),
                            'theme': theme,
                            'tag': t,
                            'description': f"Field {column_name} from {theme}/{t}"
                        }
                    
                    schemas[t] = schema_info
                    logger.info(f"Successfully retrieved schema for {theme}/{t}")
                    
                except Exception as e:
                    logger.error(f"Error fetching schema for {theme}/{t}: {e}")
                    schemas[t] = {"error": str(e)}
            
            return schemas
            
        except Exception as e:
            logger.error(f"Error getting schema for theme {theme}: {e}")
            return {}

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all themes and their types.
        
        Returns:
            Nested dictionary containing schemas for all themes and types
        """
        try:
            all_schemas = {}
            for theme in self.THEMES:
                logger.info(f"Fetching schemas for theme: {theme}")
                theme_schemas = self.get_theme_schema(theme)
                if theme_schemas:
                    all_schemas[theme] = theme_schemas
            
            return all_schemas
            
        except Exception as e:
            logger.error(f"Error fetching all schemas: {e}")
            return {}

    def get_schema_metadata(self, themes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get schema metadata for specified themes or all themes.
        
        Args:
            themes: Optional list of theme names. If None, gets schema for all themes.
            
        Returns:
            Dictionary containing processed schema metadata with executable template
        """
        try:
            logger.info(f"Starting schema metadata extraction. Requested themes: {themes if themes else 'all'}")
            
            # Initialize result dictionary
            schema_metadata = {}
            logger.debug("Initialized empty schema metadata dictionary")
            
            # Get raw schema data using existing methods
            if themes:
                logger.info(f"Fetching schemas for specific themes: {themes}")
                raw_schemas = {}
                for theme in themes:
                    theme_schema = self.get_theme_schema(theme)
                    if theme_schema:
                        raw_schemas[theme] = theme_schema
                        logger.info(f"Successfully fetched schema for theme: {theme}")
                    else:
                        logger.warning(f"Failed to fetch schema for theme: {theme}")
            else:
                logger.info("Fetching schemas for all themes")
                raw_schemas = self.get_all_schemas()
                logger.info(f"Successfully fetched schemas for {len(raw_schemas)} themes")
            
            # Process the raw schemas
            for theme, theme_data in raw_schemas.items():
                logger.info(f"Processing theme: {theme}")
                
                # Process each type within theme
                for type_name, fields in theme_data.items():
                    logger.debug(f"Processing type '{type_name}' in theme '{theme}'")
                    
                    # Process each field
                    field_count = 0
                    for field_name, field_meta in fields.items():
                        logger.debug(f"Processing field: {field_name}")
                        
                        # Create executable template
                        bbox_template = "bbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}"
                        function_call = f"api.download_theme_type(theme='{theme}', tag='{type_name}', bbox=bbox)"
                        
                        # Combine all metadata under a single metadata section
                        metadata = {
                            "type": field_meta.get("type"),
                            "nullable": field_meta.get("nullable"),
                            "description": field_meta.get("description"),
                            "theme": theme,
                            "tag": type_name,
                            # Add executable metadata fields
                            "import": "from memories.data_acquisition.sources.overture_api import OvertureConnector",
                            "function": "download_theme_type",
                            "parameters": f"""
# Initialize API
api = OvertureConnector()

# Create bbox from existing coordinates
{bbox_template}

# Download data
{function_call}
"""
                        }
                        
                        # Store in result dictionary with new structure
                        schema_metadata[field_name] = {
                            "metadata": metadata
                        }
                        
                        field_count += 1
                    
                    logger.info(f"Processed {field_count} fields for {theme}/{type_name}")
            
            # Save to JSON file
            output_file = self.data_dir / 'schema_metadata.json'
            logger.info(f"Saving schema metadata to {output_file}")
            
            with open(output_file, 'w') as f:
                json.dump(schema_metadata, f, indent=2)
            
            logger.info(f"Successfully saved schema metadata with {len(schema_metadata)} total fields")
            return schema_metadata
            
        except Exception as e:
            logger.error(f"Error processing schema metadata: {e}", exc_info=True)
            return {}

    def validate_bbox(self, bbox: Dict[str, float]) -> bool:
        """Validate bounding box coordinates.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            
        Returns:
            bool: True if bbox is valid
        """
        try:
            # Check coordinate ranges
            if not (-180 <= bbox['xmin'] <= 180 and -180 <= bbox['xmax'] <= 180):
                logger.error("Invalid longitude values. Must be between -180 and 180.")
                return False
                
            if not (-90 <= bbox['ymin'] <= 90 and -90 <= bbox['ymax'] <= 90):
                logger.error("Invalid latitude values. Must be between -90 and 90.")
                return False
                
            # Check that min is less than max
            if bbox['xmin'] >= bbox['xmax']:
                logger.error("xmin must be less than xmax")
                return False
                
            if bbox['ymin'] >= bbox['ymax']:
                logger.error("ymin must be less than ymax")
                return False
                
            return True
            
        except KeyError as e:
            logger.error(f"Missing required bbox coordinate: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating bbox: {e}")
            return False

    def download_theme_type(self, theme: str, type_name: str, bbox: Dict[str, float]) -> bool:
        """Download data for a specific theme and type with bbox filtering.
        
        Args:
            theme: Theme name
            type_name: Type name within theme
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            
        Returns:
            bool: True if download successful
        """
        if theme not in self.THEMES:
            logger.error(f"Invalid theme: {theme}")
            return False
            
        if type_name not in self.THEMES[theme]:
            logger.error(f"Invalid tag {type_name} for theme {theme}")
            return False
            
        if not self.validate_bbox(bbox):
            return False
            
        try:
            logger.info(f"Starting download for {theme}/{type_name}")
            s3_path = self.get_s3_path(theme, type_name)
            logger.info(f"Using S3 path: {s3_path}")
            
            # Create output directory
            storage_dir = self.data_dir / theme / type_name
            storage_dir.mkdir(parents=True, exist_ok=True)
            output_file = storage_dir / f"{type_name}_filtered.parquet"
            logger.info(f"Output will be saved to: {output_file}")
            
            # Test S3 access
            test_query = f"""
            SELECT COUNT(*) 
            FROM read_parquet('{s3_path}', filename=true, hive_partitioning=1)
            LIMIT 1
            """
            
            try:
                logger.info(f"Testing S3 access for {theme}/{type_name}...")
                self.con.execute(test_query)
            except Exception as e:
                logger.error(f"Failed to access S3 path for {theme}/{type_name}: {e}")
                return False
            
            # Query to filter and download data
            query = f"""
            COPY (
                SELECT 
                    id, 
                    names.primary AS primary_name,
                    geometry,
                    *
                FROM 
                    read_parquet('{s3_path}', filename=true, hive_partitioning=1)
                WHERE 
                    bbox.xmin >= {bbox['xmin']}
                    AND bbox.xmax <= {bbox['xmax']}
                    AND bbox.ymin >= {bbox['ymin']}
                    AND bbox.ymax <= {bbox['ymax']}
            ) TO '{output_file}' (FORMAT 'parquet');
            """
            
            logger.info(f"Downloading filtered data for {theme}/{type_name}...")
            try:
                self.con.execute(query)
                
                # Verify the file was created and has content
                if output_file.exists() and output_file.stat().st_size > 0:
                    count_query = f"SELECT COUNT(*) as count FROM read_parquet('{output_file}')"
                    count = self.con.execute(count_query).fetchone()[0]
                    logger.info(f"Successfully saved {count} features for {theme}/{type_name}")
                    return True
                else:
                    logger.warning(f"No features found for {theme}/{type_name}")
                    return True  # Still return True as the operation completed successfully
            except Exception as e:
                logger.error(f"Error downloading {theme}/{type_name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading {theme}/{type_name} data: {e}")
            return False

    def search_features_by_type(self, feature_type: str, bbox: Union[List[float], Dict[str, float]]) -> Dict[str, Any]:
        """
        Search for specific features (like parks, roads, etc.) within a bounding box.
        
        Args:
            feature_type: Type of feature to search for (e.g., "parks", "roads", "buildings")
            bbox: Bounding box as either:
                 - List [min_lon, min_lat, max_lon, max_lat]
                 - Dict with keys 'xmin', 'ymin', 'xmax', 'ymax'
            
        Returns:
            Dictionary containing matching features
        """
        try:
            # Convert bbox to dictionary format if it's a list
            if isinstance(bbox, (list, tuple)):
                bbox_dict = {
                    "xmin": bbox[0],
                    "ymin": bbox[1],
                    "xmax": bbox[2],
                    "ymax": bbox[3]
                }
            else:
                bbox_dict = bbox
            
            # Map common feature types to Overture themes and tags
            feature_mapping = {
                "parks": {"theme": "places", "tags": ["place"], "filters": ["leisure=park", "landuse=recreation_ground"]},
                "roads": {"theme": "transportation", "tags": ["segment"], "filters": ["highway"]},
                "buildings": {"theme": "buildings", "tags": ["building"], "filters": []},
                "water": {"theme": "base", "tags": ["water"], "filters": []},
                "land": {"theme": "base", "tags": ["land", "land_use", "land_cover"], "filters": []},
                "addresses": {"theme": "addresses", "tags": ["address"], "filters": []}
            }
            
            if feature_type.lower() not in feature_mapping:
                logger.error(f"Unsupported feature type: {feature_type}")
                return {"error": f"Unsupported feature type. Supported types are: {list(feature_mapping.keys())}"}
            
            mapping = feature_mapping[feature_type.lower()]
            theme = mapping["theme"]
            tags = mapping["tags"]
            filters = mapping["filters"]
            
            # Create theme directory if it doesn't exist
            theme_dir = self.data_dir / theme
            theme_dir.mkdir(parents=True, exist_ok=True)
            
            results = []
            for tag in tags:
                parquet_file = theme_dir / f"{tag}_filtered.parquet"
                
                # Download data if it doesn't exist
                if not parquet_file.exists():
                    success = self.download_theme_type(theme, tag, bbox_dict)
                    if not success:
                        logger.warning(f"Failed to download data for {theme}/{tag}")
                        continue
                
                try:
                    # Build query with filters if any
                    filter_conditions = ""
                    if filters:
                        filter_conditions = " AND (" + " OR ".join([
                            f"class LIKE '%{f}%' OR subclass LIKE '%{f}%'"
                            for f in filters
                        ]) + ")"
                    
                    query = f"""
                    SELECT 
                        id,
                        names.primary AS name,
                        geometry,
                        class,
                        subclass,
                        *
                    FROM read_parquet('{parquet_file}')
                    WHERE 1=1 {filter_conditions}
                    """
                    
                    df = self.con.execute(query).fetchdf()
                    if not df.empty:
                        results.extend(df.to_dict('records'))
                        logger.info(f"Found {len(df)} {feature_type} features in {tag}")
                except Exception as e:
                    logger.warning(f"Error reading {parquet_file}: {str(e)}")
            
            return {
                "type": feature_type,
                "count": len(results),
                "features": results
            }
            
        except Exception as e:
            logger.error(f"Error searching for {feature_type}: {str(e)}")
            return {"error": str(e)}


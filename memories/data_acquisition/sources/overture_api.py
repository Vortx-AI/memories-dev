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

class OvertureAPI:
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
                    parquet_file = theme_dir / f"{type_name}_filtered.parquet"
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
                            "import": "from memories.data_acquisition.sources.overture_api import OvertureAPI",
                            "function": "download_theme_type",
                            "parameters": f"""
# Initialize API
api = OvertureAPI()

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

    def download_theme_type(self, theme: str, tag: str, bbox: Dict[str, float], storage_path: Optional[str] = None, max_size: int = 1024*1024*1024) -> bool:
        """Download data for a specific theme and type (tag) with bbox filtering.
        
        Args:
            theme: Theme name (e.g., 'buildings', 'places')
            tag: Type/tag name (e.g., 'building', 'place')
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            storage_path: Optional path for storage. If None, uses self.data_dir
            max_size: Maximum size for cold storage in bytes (default: 1GB)
        
        Returns:
            bool: True if download successful
        """
        try:
            logger.info(f"Starting download for {theme}/{tag}")
            
            # Validate theme and tag
            if theme not in self.THEMES:
                logger.error(f"Invalid theme: {theme}")
                return False
            
            if tag not in self.THEMES[theme]:
                logger.error(f"Invalid tag {tag} for theme {theme}")
                return False
            
            # Get S3 path for the specific theme and tag
            s3_path = self.get_s3_path(theme, tag)
            logger.info(f"Using S3 path: {s3_path}")
            
            # Use provided storage path or default to self.data_dir
            storage_path = Path(storage_path) if storage_path else Path(self.data_dir)
            
            # Initialize ColdMemory with Path object
            cold_storage = ColdMemory(storage_path, max_size=max_size)
            
            # Create theme/tag directory in cold storage
            output_dir = storage_path / "overture" / theme / tag
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Define output file path
            output_file = output_dir / f"{tag}_filtered.parquet"
            logger.info(f"Output will be saved to: {output_file}")
            
            # Test S3 access
            test_query = f"""
            SELECT COUNT(*) 
            FROM read_parquet('{s3_path}', filename=true, hive_partitioning=1)
            LIMIT 1
            """
            
            try:
                logger.info(f"Testing S3 access for {theme}/{tag}...")
                self.con.execute(test_query)
            except Exception as e:
                logger.error(f"Failed to access S3 path for {theme}/{tag}: {e}")
                return False
            
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
            
            logger.info(f"Downloading filtered data for {theme}/{tag}...")
            try:
                self.con.execute(query)
                
                # Verify the file was created and has content
                if output_file.exists() and output_file.stat().st_size > 0:
                    count_query = f"SELECT COUNT(*) as count FROM read_parquet('{output_file}')"
                    count = self.con.execute(count_query).fetchone()[0]
                    logger.info(f"Successfully saved {count} features for {theme}/{tag}")
                    
                    # Store metadata in cold storage
                    metadata = {
                        "theme": theme,
                        "tag": tag,
                        "bbox": bbox,
                        "count": count,
                        "timestamp": str(datetime.now()),
                        "file_path": str(output_file)
                    }
                    
                    # Store using the store property
                    cold_storage.store = {f"overture_{theme}_{tag}": metadata}
                    
                    return True
                else:
                    logger.warning(f"No features found for {theme}/{tag} in the specified bbox")
                    return False
                
            except Exception as e:
                logger.error(f"Error downloading {theme}/{tag}: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Error in download_theme_type: {e}", exc_info=True)
            return False

    